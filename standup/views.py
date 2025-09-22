
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from config.demo_time import now as demo_now
from datetime import timedelta
import json
import pytz

from dashboard.models import StandupSession, Project, TeamMember, WorkItemReference, Blocker
from dashboard.services import MVPTeamHealthService


class StandupReportView(LoginRequiredMixin, TemplateView):
    """Dedicated view for standup reports. Falls back to demo data if requested or no project assigned."""
    template_name = "standup/standup_report.html"
    login_url = '/auth/login/'
    redirect_field_name = 'next'

    def dispatch(self, request, *args, **kwargs):
        # Allow demo mode without authentication
        if request.GET.get('demo') == 'true':
            return TemplateView.dispatch(self, request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def _resolve_project_for_context(self):
        """Resolve which project to source data from, allowing demo fallback."""
        demo_mode = self.request.GET.get('demo') == 'true'
        try:
            if not demo_mode:
                team_member = TeamMember.objects.get(user=self.request.user)
                return team_member.project, False
        except TeamMember.DoesNotExist:
            # Fall through to demo resolution
            pass

        # For demo: Use the MVP Team Health Project where our test data is located
        project = (
            Project.objects.filter(name='MVP Team Health Project').first()
            or Project.objects.filter(name='PulzeBot AI Pipeline Demo').first()
            or Project.objects.filter(status='active').first()
        )
        return project, True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project, used_demo = self._resolve_project_for_context()
        if not project:
            # No data available at all
            context['no_project'] = True
            context['error_message'] = "No project data available. Run demo data setup to populate sample data."
            return context

        try:
                # Get today's date in Singapore timezone for proper filtering
                singapore_tz = pytz.timezone('Asia/Singapore')
                singapore_now = demo_now().astimezone(singapore_tz)
                today = singapore_now.date()
                week_start = today - timedelta(days=6)  # Past 7 days including today
                
                # Get recent standup sessions (past week for better data display)
                recent_sessions = StandupSession.objects.filter(
                    project=project,
                    date__gte=week_start
                ).order_by('-date')
                
                # Get today's sessions only (for Daily tab)
                today_sessions = StandupSession.objects.filter(
                    project=project,
                    date=today
                ).order_by('-date', 'user__username')
                
                # Get team standup sessions for past week (for Weekly tab calculations)
                weekly_sessions = StandupSession.objects.filter(
                    project=project,
                    date__gte=week_start
                ).order_by('-date', 'user__username')
                
                # Get work item statistics for past week
                work_item_refs = WorkItemReference.objects.filter(
                    standup_session__project=project,
                    standup_session__date__gte=week_start
                )
                
                # Calculate statistics (today's stats for header)
                total_standups = today_sessions.count()
                completed_standups = today_sessions.filter(status='completed').count()
                completion_rate = (completed_standups / total_standups * 100) if total_standups > 0 else 0

                # Work item stats by type
                work_item_stats = {}
                for ref in work_item_refs:
                    item_type = ref.item_type
                    if item_type not in work_item_stats:
                        work_item_stats[item_type] = 0
                    work_item_stats[item_type] += 1
                
                # Get top work items by mention frequency
                from django.db.models import Count
                items_agg = WorkItemReference.objects.filter(
                    standup_session__project=project,
                    standup_session__date=today
                ).values('item_id', 'item_type', 'title').annotate(
                    mention_count=Count('id')
                ).order_by('-mention_count')[:10]

                def _display_name(item_type: str, item_id: str) -> str:
                    t = (item_type or '').lower()
                    if t == 'github_pr':
                        return f"PR #{item_id}"
                    if t == 'github_issue':
                        return f"Issue #{item_id}"
                    if t == 'jira_ticket':
                        return item_id
                    if t == 'branch':
                        return f"Branch: {item_id}"
                    return item_id

                top_work_items = [
                    {
                        'item_id': row['item_id'],
                        'item_type': row['item_type'],
                        'display_name': _display_name(row['item_type'], row['item_id']),
                        'title': row['title'],
                        'mention_count': row['mention_count'],
                    }
                    for row in items_agg
                ]
                
                # Map to template-friendly demo structure used by standup_report.html
                standup_reports = []
                def get_mood_emoji(mood):
                    mood_emojis = {
                        'excited': '🚀',
                        'productive': '💪',
                        'focused': '🎯',
                        'neutral': '😐',
                        'tired': '😴',
                        'frustrated': '😤',
                        'blocked': '🚧',
                        'overwhelmed': '😰'
                    }
                    return mood_emojis.get(mood.lower(), '😐')
                
                from datetime import datetime, time as dtime
                import random

                # Generate Daily reports from today's sessions only
                for s in today_sessions:
                    mood = s.sentiment_label or 'neutral'

                    # Always generate a consistent-but-varied time per session
                    # Use session id and date to seed, so multiple sessions per day differ
                    seed_value = ((getattr(s, 'id', 0) or 0) * 10007) + s.date.toordinal()
                    rng = random.Random(seed_value)
                    hour = rng.randint(8, 18)
                    minute = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
                    # Create timestamp in Singapore timezone
                    singapore_tz = pytz.timezone('Asia/Singapore')
                    naive_dt = datetime.combine(s.date, dtime(hour=hour, minute=minute))
                    ts = singapore_tz.localize(naive_dt)

                    # Convert BERT score to sentiment label and display
                    bert_score = float(s.sentiment_score) if s.sentiment_score else 0.5
                    
                    # Map BERT score to sentiment label  
                    if bert_score >= 0.8:
                        bert_sentiment = 'Very Positive'
                        bert_color = 'success'
                    elif bert_score >= 0.6:
                        bert_sentiment = 'Positive'
                        bert_color = 'success'
                    elif bert_score >= 0.4:
                        bert_sentiment = 'Neutral'
                        bert_color = 'secondary'
                    elif bert_score >= 0.2:
                        bert_sentiment = 'Negative'
                        bert_color = 'danger'
                    else:
                        bert_sentiment = 'Very Negative'
                        bert_color = 'danger'
                    
                    bert_display = f"{bert_sentiment} ({bert_score:.2f})"
                    
                    standup_reports.append({
                        'user': s.user.username,
                        'timestamp': ts,
                        'mood': mood,
                        'bert_sentiment_display': bert_display,
                        'bert_color': bert_color,
                        'bert_score': bert_score,
                        'has_blockers': bool(s.blockers and s.blockers.strip()),
                        # completion removed from UI; keep value for potential analytics
                        'completion_score': min(100, max(10, (len((s.yesterday_work or '')) + len((s.today_plan or ''))) // 5)),
                        'yesterday': s.yesterday_work or '',
                        'today': s.today_plan or '',
                        'blockers': s.blockers or '',
                        'blocker_priority': 'medium',
                        'blocker_impact': 'moderate',
                        'ai_insights': s.ai_summary or '',
                        'action_items': [],
                        'yesterday_tasks': [],
                        'today_tasks': [],
                    })

                # Sort standup reports by timestamp (newest first)
                standup_reports.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Generate weekly standup reports
                weekly_standup_reports = self._generate_weekly_reports(project, today)
                
                # Generate all-time standup reports
                all_time_standup_reports = self._generate_all_time_reports(project)
                
                # Generate blocker-only reports (now using Blocker model)
                blocker_reports = self._generate_blocker_reports_v2(project)
                
                # Get actual Blocker objects for template (template expects Django models)
                # Get all blockers for this project (we'll filter by recency in template if needed)
                all_blockers = Blocker.objects.filter(
                    standup_session__project=project
                ).select_related('standup_session__user', 'resolved_by').order_by('-created_at')
                
                # Get only active blockers for display
                active_blockers_queryset = all_blockers.filter(status='active')

                # Quick stats for header cards
                team_members_count = TeamMember.objects.filter(project=project, is_active=True).count()
                submitted_today = StandupSession.objects.filter(project=project, date=today, status='completed').count()
                # Count actual active Blocker objects (persistent across dates)
                active_blockers = active_blockers_queryset.count()
                
                # Normalise sentiment to 0..10 mood scale for averages
                def to_mood10(sess):
                    raw = sess.sentiment_score
                    if raw is not None:
                        score = float(raw)
                        if 0.0 <= score <= 1.0:
                            mood10_val = score * 10.0
                        elif -1.0 <= score <= 1.0:
                            mood10_val = ((score + 1.0) / 2.0) * 10.0
                        else:
                            mood10_val = max(0.0, min(10.0, score))
                    else:
                        mapping = {
                            'excited': 0.9,
                            'productive': 0.8,
                            'focused': 0.7,
                            'neutral': 0.5,
                            'tired': 0.35,
                            'frustrated': 0.25,
                            'blocked': 0.2,
                            'overwhelmed': 0.15,
                        }
                        score = mapping.get((sess.sentiment_label or 'neutral').lower(), 0.5)
                        mood10_val = score * 10.0
                    return round(mood10_val, 1)

                # Use BERT sentiment scores for Team Health (match dashboard: use today's sessions)
                bert_sessions = today_sessions.filter(sentiment_score__isnull=False)
                
                if bert_sessions.exists():
                    # Use individual BERT scores (already 0-1 scale) and convert to 0-10
                    individual_scores = [float(s.sentiment_score) for s in bert_sessions]
                    avg_mood_score = round(sum(individual_scores) / len(individual_scores) * 10, 1)
                else:
                    # Fallback to mood labels if no BERT scores available
                    mood_mapping = {
                        'excited': 0.9, 'productive': 0.8, 'focused': 0.7, 'neutral': 0.5,
                        'tired': 0.35, 'frustrated': 0.25, 'blocked': 0.2, 'overwhelmed': 0.15,
                    }
                    mood_scores = [mood_mapping.get((s.sentiment_label or 'neutral').lower(), 0.5) * 10 
                                 for s in today_sessions]
                    if mood_scores:
                        avg_mood_score = round(sum(mood_scores) / len(mood_scores), 1)
                    else:
                        avg_mood_score = 7.0

                # Build chart data from standup sessions (demo or real)
                from collections import defaultdict
                import json as _json

                # Sentiment per day → mood score 0-10
                label_to_score = {
                    'excited': 0.9,
                    'productive': 0.8,
                    'focused': 0.7,
                    'neutral': 0.5,
                    'tired': 0.35,
                    'frustrated': 0.25,
                    'blocked': 0.2,
                    'overwhelmed': 0.15,
                }

                daily_sentiments = defaultdict(list)
                for sess in weekly_sessions:
                    raw = sess.sentiment_score
                    if raw is not None:
                        score = float(raw)
                        # Normalise: if score is already 0..1 → 0..10, else if -1..1 → map to 0..10
                        if 0.0 <= score <= 1.0:
                            mood10 = score * 10.0
                        elif -1.0 <= score <= 1.0:
                            mood10 = ((score + 1.0) / 2.0) * 10.0
                        else:
                            # Fallback clamp
                            mood10 = max(0.0, min(10.0, score))
                    else:
                        score = label_to_score.get((sess.sentiment_label or 'neutral').lower(), 0.5)
                        mood10 = score * 10.0
                    daily_sentiments[sess.date].append(round(mood10, 1))

                # Update mood trends to show past week data
                weekly_sentiment_data = self._calculate_weekly_mood_trends(project, today)
                trend_labels = weekly_sentiment_data['labels']
                trend_values = weekly_sentiment_data['values']

                # Update blocker categories to include all blockers regardless of submission date
                blocker_counts = self._calculate_all_time_blocker_categories(project)

                trend_chart_json = _json.dumps({'labels': trend_labels, 'data': trend_values})
                blocker_chart_json = _json.dumps({'labels': list(blocker_counts.keys()), 'data': list(blocker_counts.values())})

                context.update({
                    'project': project,
                    'recent_sessions': recent_sessions[:10],  # Latest 10 sessions
                    'team_sessions': weekly_sessions,  # For backward compatibility with template
                    'standup_reports': standup_reports,
                    'weekly_standup_reports': weekly_standup_reports,
                    'all_time_standup_reports': all_time_standup_reports,
                    'blocker_reports': blocker_reports,
                    'blockers': all_blockers,  # Template expects Django model objects (all recent blockers)
                    'active_blockers_list': active_blockers_queryset,  # Only active blockers for display
                    'team_members_count': team_members_count,
                    'submitted_today': submitted_today,
                    'active_blockers': active_blockers,
                    'avg_mood_score': avg_mood_score,
                    'selected_date': today,
                    'total_standups': total_standups,
                    'completed_standups': completed_standups,
                    'completion_rate': round(completion_rate, 1),
                    'work_item_stats': work_item_stats,
                    'top_work_items': top_work_items,
                    'date_range': {
                        'start': today,
                        'end': today
                    },
                    'trend_chart_json': trend_chart_json,
                    'blocker_chart_json': blocker_chart_json,
                })

                # Add team health metrics for Period comparison chart
                try:
                    service = MVPTeamHealthService(project)
                    context['metrics_7d'] = service.get_mvp_metrics(days_back=7)  # 7 days data
                    context['metrics_30d'] = service.get_mvp_metrics(days_back=30)  # 30 days data
                except Exception as e:
                    # Fallback to empty metrics if service fails
                    context['metrics_7d'] = {}
                    context['metrics_30d'] = {}

                # Add Gemini AI summaries for AI-Powered Team Insights
                context['gemini_summaries'] = self._get_gemini_summaries(project)

                # Flag demo mode to templates if applicable
                context['demo_mode'] = used_demo or (self.request.GET.get('demo') == 'true')

        except Exception as e:
            # Handle any other exceptions
            context['no_project'] = True
            context['error_message'] = f"Error loading standup reports: {str(e)}"
        
        return context

    def _get_gemini_summaries(self, project):
        """Get comprehensive AI summaries with all necessary data as per Deep Research document requirements."""
        end_date = demo_now().date()
        start_date = end_date - timedelta(days=7)

        # Get recent standup sessions (use all sessions if no AI summaries available)
        sessions_with_summaries = StandupSession.objects.filter(
            project=project,
            date__range=[start_date, end_date],
            ai_summary__isnull=False
        ).exclude(ai_summary='').select_related('user').order_by('-date')[:5]
        
        # If no AI summaries, use regular standup sessions
        if not sessions_with_summaries.exists():
            sessions_with_summaries = StandupSession.objects.filter(
                project=project,
                date__range=[start_date, end_date]
            ).select_related('user').order_by('-date')[:5]

        # Get all work item references for the window
        from dashboard.models import WorkItemReference
        from django.db.models import Count

        window_refs = WorkItemReference.objects.filter(
            standup_session__project=project,
            standup_session__date__range=[start_date, end_date]
        ).select_related('standup_session__user')

        # Aggregate work items per user and type
        counts_by_user = {}
        for ref in window_refs.values('standup_session__user__id', 'item_type').annotate(c=Count('id')):
            uid = ref['standup_session__user__id']
            counts_by_user.setdefault(uid, {'github_pr': 0, 'github_issue': 0, 'jira_ticket': 0, 'other': 0})
            t = (ref['item_type'] or '').lower()
            if t in counts_by_user[uid]:
                counts_by_user[uid][t] += ref['c']
            else:
                counts_by_user[uid]['other'] += ref['c']

        # Get top 3 work items per user by mention frequency
        top_items_by_user = {}
        for row in window_refs.values('standup_session__user__id', 'item_type', 'item_id', 'title', 'status').annotate(mention_count=Count('id')).order_by('-mention_count'):
            uid = row['standup_session__user__id']
            top_items_by_user.setdefault(uid, [])
            if len(top_items_by_user[uid]) < 3:
                # Calculate ETA for this specific item
                item_type = (row['item_type'] or '').lower()
                status = (row['status'] or '').lower()
                
                # Base ETA by type and status
                if 'pr' in item_type:
                    if 'review' in status or 'approved' in status:
                        eta = "~1 day"
                    elif 'draft' in status:
                        eta = "~2-3 days"
                    else:
                        eta = "~1-2 days"
                elif 'issue' in item_type:
                    if 'in_progress' in status:
                        eta = "~2-3 days"
                    elif 'open' in status:
                        eta = "~3-5 days"
                    else:
                        eta = "~2-4 days"
                elif 'jira' in item_type:
                    if 'in_progress' in status:
                        eta = "~3-5 days"
                    elif 'to_do' in status:
                        eta = "~5-7 days"
                    else:
                        eta = "~3-7 days"
                else:
                    eta = "~3-5 days"
                
                top_items_by_user[uid].append({
                    'item_type': row['item_type'],
                    'item_id': row['item_id'],
                    'title': row['title'],
                    'status': row['status'],
                    'mention_count': row['mention_count'],
                    'eta': eta,
                })

        # Get all sessions for plan-vs-done reconciliation
        sessions_window = StandupSession.objects.filter(
            project=project,
            date__range=[start_date, end_date]
        ).select_related('user').order_by('user__id', 'date')

        by_user_by_date = {}
        for s in sessions_window:
            by_user_by_date.setdefault(s.user_id, {})[s.date] = s



        def calculate_eta_for_items(items):
            """Calculate ETAs for top work items based on type and status."""
            if not items:
                return "No ETAs available"
            
            etas = []
            for it in items[:3]:
                item_type = (it.get('item_type') or '').lower()
                item_id = it.get('item_id', '')
                status = (it.get('status') or '').lower()
                
                # Base ETA by type
                if 'pr' in item_type:
                    if 'review' in status or 'approved' in status:
                        eta = "~1 day"
                    elif 'draft' in status:
                        eta = "~2-3 days"
                    else:
                        eta = "~1-2 days"
                elif 'issue' in item_type:
                    if 'in_progress' in status:
                        eta = "~2-3 days"
                    elif 'open' in status:
                        eta = "~3-5 days"
                    else:
                        eta = "~2-4 days"
                elif 'jira' in item_type:
                    if 'in_progress' in status:
                        eta = "~3-5 days"
                    elif 'to_do' in status:
                        eta = "~5-7 days"
                    else:
                        eta = "~3-7 days"
                else:
                    eta = "~3-5 days"
                
                etas.append(f"{item_id}: {eta}")
            
            return "; ".join(etas)



        def get_individual_updates(session):
            """Get yesterday's work, today's plan, and blockers for individual updates."""
            yesterday_work = session.yesterday_work or "No reported activity."
            today_plan = session.today_plan or "No reported plans."
            blockers = session.blockers or "None"
            
            return {
                'yesterday_work': yesterday_work,
                'today_plan': today_plan,
                'blockers': blockers
            }

        summaries = []
        for session in sessions_with_summaries:
            user = session.user
            uid = user.id
            counts = counts_by_user.get(uid, {})
            top_items = top_items_by_user.get(uid, [])
            
            # Get individual updates from most recent session
            updates = get_individual_updates(session)
            
            # Build comprehensive integration summary
            if counts:
                gh_pr = counts.get('github_pr', 0)
                gh_issue = counts.get('github_issue', 0)
                jira = counts.get('jira_ticket', 0)
                other = counts.get('other', 0)
                parts = []
                if gh_pr: parts.append(f"PRs: {gh_pr}")
                if gh_issue: parts.append(f"Issues: {gh_issue}")
                if jira: parts.append(f"Jira: {jira}")
                if other: parts.append(f"Other: {other}")
                counts_str = ", ".join(parts) if parts else "No referenced work items"
            else:
                counts_str = "No referenced work items"

            # Top work items summary
            if top_items:
                top_str = "; ".join([
                    f"{(ti['item_type'] or '').replace('_',' ').title()} {ti['item_id']}: {ti['title']}"
                    for ti in top_items
                ])
            else:
                top_str = ""

            integration_summary = f"GitHub/Jira activity (7d): {counts_str}"
            if top_str:
                integration_summary += f". Top items: {top_str}"

            # Calculate ETAs
            eta_summary = calculate_eta_for_items(top_items)

            # Calculate weekly BERT sentiment average (same as Team Dashboard)
            today = demo_now().date()
            week_start = today - timedelta(days=6)  # Past 7 days including today
            weekly_sessions = StandupSession.objects.filter(
                project=project,
                user=user,
                date__gte=week_start,
                date__lte=today
            )
            
            mood_scores = []
            for weekly_session in weekly_sessions:
                if weekly_session.sentiment_score:
                    mood_scores.append(float(weekly_session.sentiment_score) * 10)
                else:
                    # Fallback to label-based scoring (same as Team Dashboard)
                    label_to_score = {
                        'excited': 9.0, 'productive': 8.0, 'focused': 7.0, 'neutral': 5.0,
                        'tired': 3.5, 'frustrated': 2.5, 'blocked': 2.0, 'overwhelmed': 1.5,
                    }
                    mood_scores.append(label_to_score.get((weekly_session.sentiment_label or 'neutral').lower(), 5.0))
            
            weekly_bert_avg = round(sum(mood_scores) / len(mood_scores), 1) if mood_scores else 5.0
            # Convert back to 0-1 scale for consistency
            weekly_bert_score = weekly_bert_avg / 10

            # Aggregate blockers from weekly sessions (same as Team Dashboard)
            weekly_blockers = []
            for weekly_session in weekly_sessions:
                if weekly_session.blockers and weekly_session.blockers.strip():
                    weekly_blockers.append(weekly_session.blockers.strip())
            
            # Update blockers to show weekly aggregated blockers
            if weekly_blockers:
                updates['blockers'] = '; '.join(weekly_blockers)
            else:
                updates['blockers'] = 'None'

            # Generate AI summary from standup data if not available
            if session.ai_summary:
                summary = session.ai_summary
            else:
                # Create a summary from standup data
                summary_parts = []
                if updates['yesterday_work'] and updates['yesterday_work'] != "No reported activity.":
                    summary_parts.append(f"Completed: {updates['yesterday_work']}")
                if updates['today_plan'] and updates['today_plan'] != "No reported plans.":
                    summary_parts.append(f"Planning: {updates['today_plan']}")
                if updates['blockers'] and updates['blockers'] != "None":
                    summary_parts.append(f"Blockers: {updates['blockers']}")
                
                if summary_parts:
                    summary = " ".join(summary_parts)
                else:
                    summary = f"Standup update for {user.get_full_name() or user.username} on {session.date}"

            summaries.append({
                'user': user.get_full_name() or user.username,
                'date': session.date,
                'summary': summary,
                'sentiment': session.sentiment_label,
                'sentiment_score': weekly_bert_score,  # Use weekly BERT average
                'integration_summary': integration_summary,
                'eta_summary': eta_summary,
                'individual_updates': updates,
                'work_items': top_items,
                'work_item_counts': counts,
            })

        return summaries
    
    def _generate_weekly_reports(self, project, today):
        """Generate weekly aggregated standup reports for the past 7 days."""
        from datetime import datetime, time as dtime
        
        weekly_reports = []
        week_start = today - timedelta(days=6)  # Past 7 days including today
        
        # Get all sessions for the past week
        weekly_sessions = StandupSession.objects.filter(
            project=project,
            date__gte=week_start,
            date__lte=today
        ).order_by('user__username', 'date')
        
        # Group by user
        from collections import defaultdict
        user_sessions = defaultdict(list)
        for session in weekly_sessions:
            user_sessions[session.user.username].append(session)
        
        for username, sessions in user_sessions.items():
            if not sessions:
                continue
                
            # Calculate weekly aggregations
            total_sessions = len(sessions)
            
            # Aggregate accomplishments (yesterday_work from all sessions)
            accomplishments = []
            for session in sessions:
                if session.yesterday_work and session.yesterday_work.strip():
                    accomplishments.append(f"• {session.yesterday_work.strip()}")
            
            # Get current focus (today_plan from most recent session)
            current_focus = ""
            if sessions:
                latest_session = max(sessions, key=lambda s: s.date)
                current_focus = latest_session.today_plan or ""
            
            # Aggregate blockers
            blockers = []
            for session in sessions:
                if session.blockers and session.blockers.strip():
                    blockers.append(session.blockers.strip())
            
            # Calculate average mood
            mood_scores = []
            for session in sessions:
                if session.sentiment_score:
                    mood_scores.append(float(session.sentiment_score) * 10)
                else:
                    # Fallback to label-based scoring
                    label_to_score = {
                        'excited': 9.0, 'productive': 8.0, 'focused': 7.0, 'neutral': 5.0,
                        'tired': 3.5, 'frustrated': 2.5, 'blocked': 2.0, 'overwhelmed': 1.5,
                    }
                    mood_scores.append(label_to_score.get((session.sentiment_label or 'neutral').lower(), 5.0))
            
            avg_mood = round(sum(mood_scores) / len(mood_scores), 1) if mood_scores else 5.0
            
            # Get most recent session date for this user
            most_recent_session = max(sessions, key=lambda s: s.date)
            
            weekly_reports.append({
                'user': username,
                'sessions_count': total_sessions,
                'week_start': week_start,
                'yesterday': '\n'.join(accomplishments) if accomplishments else 'No accomplishments recorded this week',
                'today': current_focus or 'No current focus specified',
                'blockers': '; '.join(blockers) if blockers else '',
                'has_blockers': bool(blockers),
                'bert_sentiment_display': f'Weekly Avg ({avg_mood:.1f}/10)',
                'bert_color': 'success' if avg_mood >= 7 else 'warning' if avg_mood >= 5 else 'danger',
                'timestamp': pytz.timezone('Asia/Singapore').localize(datetime.combine(most_recent_session.date, dtime(hour=12, minute=0))),
            })
        
        return sorted(weekly_reports, key=lambda x: x['user'])
    
    def _generate_all_time_reports(self, project):
        """Generate all-time standup reports showing complete history."""
        all_time_reports = []
        
        # Get ALL sessions for this project (no date filtering)
        all_sessions = StandupSession.objects.filter(
            project=project
        ).order_by('-date', 'user__username')
        
        # Convert sessions to same format as daily reports
        import random
        from datetime import datetime, time as dtime
        
        for session in all_sessions:
            mood = session.sentiment_label or 'neutral'
            
            # Generate consistent timestamp like in daily reports
            seed_value = ((getattr(session, 'id', 0) or 0) * 10007) + session.date.toordinal()
            rng = random.Random(seed_value)
            hour = rng.randint(8, 18)
            minute = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
            # Create timestamp in Singapore timezone
            singapore_tz = pytz.timezone('Asia/Singapore')
            naive_dt = datetime.combine(session.date, dtime(hour=hour, minute=minute))
            ts = singapore_tz.localize(naive_dt)
            
            # Convert BERT score to sentiment label and display
            bert_score = float(session.sentiment_score) if session.sentiment_score else 0.5
            
            # Map BERT score to sentiment label  
            if bert_score >= 0.8:
                bert_sentiment = 'Very Positive'
                bert_color = 'success'
            elif bert_score >= 0.6:
                bert_sentiment = 'Positive'
                bert_color = 'success'
            elif bert_score >= 0.4:
                bert_sentiment = 'Neutral'
                bert_color = 'secondary'
            elif bert_score >= 0.2:
                bert_sentiment = 'Negative'
                bert_color = 'danger'
            else:
                bert_sentiment = 'Very Negative'
                bert_color = 'danger'
            
            bert_display = f"{bert_sentiment} ({bert_score:.2f})"
            
            all_time_reports.append({
                'user': session.user.username,
                'timestamp': ts,
                'mood': mood,
                'bert_sentiment_display': bert_display,
                'bert_color': bert_color,
                'bert_score': bert_score,
                'has_blockers': bool(session.blockers and session.blockers.strip()),
                'completion_score': min(100, max(10, (len((session.yesterday_work or '')) + len((session.today_plan or ''))) // 5)),
                'yesterday': session.yesterday_work or '',
                'today': session.today_plan or '',
                'blockers': session.blockers or '',
                'blocker_priority': 'medium',
                'blocker_impact': 'moderate',
                'ai_insights': session.ai_summary or '',
                'action_items': [],
                'yesterday_tasks': [],
                'today_tasks': [],
            })
        
        # Sort by timestamp (newest first)
        all_time_reports.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_time_reports
    
    def _generate_blocker_reports_v2(self, project):
        """Generate reports showing individual blockers with resolution status."""
        blocker_reports = []
        
        # Get all individual blockers for this project (all time)
        all_blockers = Blocker.objects.filter(
            standup_session__project=project
        ).select_related('standup_session__user', 'resolved_by').order_by('-created_at')
        
        # Color mapping by category for UI badges (Bootstrap palette)
        color_by_category = {
            'Technical': 'danger',
            'Dependencies': 'warning',
            'Resources': 'info',
            'Communication': 'success',
            'Other': 'primary',
        }

        for blocker in all_blockers:
            category_display = blocker.get_category_display()
            blocker_reports.append({
                'id': blocker.id,
                'user': blocker.standup_session.user.username,
                'date': blocker.standup_session.date,
                'title': blocker.title,
                'description': blocker.description,
                'category': category_display,
                'category_color': color_by_category.get(category_display, 'secondary'),
                'status': blocker.get_status_display(),
                'is_active': blocker.is_active,
                'days_active': blocker.days_active,
                'resolved_at': blocker.resolved_at,
                'resolved_by': blocker.resolved_by.username if blocker.resolved_by else None,
                'resolution_notes': blocker.resolution_notes,
                'can_resolve': True,  # This will be updated based on user permissions in template
            })
        
        return blocker_reports
    def _calculate_weekly_mood_trends(self, project, today):
        """Calculate mood trends over the past week instead of daily."""
        week_start = today - timedelta(days=6)  # Past 7 days including today
        
        # Get sessions for the past week
        weekly_sessions = StandupSession.objects.filter(
            project=project,
            date__gte=week_start,
            date__lte=today
        )
        
        # Group by date and calculate daily averages
        from collections import defaultdict
        daily_sentiments = defaultdict(list)
        
        label_to_score = {
            'excited': 0.9, 'productive': 0.8, 'focused': 0.7, 'neutral': 0.5,
            'tired': 0.35, 'frustrated': 0.25, 'blocked': 0.2, 'overwhelmed': 0.15,
        }
        
        for sess in weekly_sessions:
            raw = sess.sentiment_score
            if raw is not None:
                score = float(raw)
                if 0.0 <= score <= 1.0:
                    mood10 = score * 10.0
                elif -1.0 <= score <= 1.0:
                    mood10 = ((score + 1.0) / 2.0) * 10.0
                else:
                    mood10 = max(0.0, min(10.0, score))
            else:
                score = label_to_score.get((sess.sentiment_label or 'neutral').lower(), 0.5)
                mood10 = score * 10.0
            daily_sentiments[sess.date].append(round(mood10, 1))
        
        # Generate labels and values for the past 7 days
        labels = []
        values = []
        
        for i in range(7):
            date = week_start + timedelta(days=i)
            labels.append(date.strftime('%b %d'))
            
            if date in daily_sentiments:
                avg_mood = round(sum(daily_sentiments[date]) / len(daily_sentiments[date]), 1)
                values.append(avg_mood)
            else:
                values.append(0)  # No data for this day
        
        return {'labels': labels, 'values': values}
    
    def _calculate_all_time_blocker_categories(self, project):
        """Calculate blocker categories from all sessions regardless of date."""
        blocker_counts = {
            'Technical': 0,
            'Dependencies': 0,
            'Resources': 0,
            'Communication': 0,
            'Other': 0,
        }
        
        # Get all sessions with blockers (all time)
        all_blocker_sessions = StandupSession.objects.filter(
            project=project,
            blockers__isnull=False
        ).exclude(blockers='')
        
        for sess in all_blocker_sessions:
            text = (sess.blockers or '').lower().strip()
            if not text:
                continue
            if any(k in text for k in ['dependency', 'blocked by', 'blocked', 'waiting for', 'awaiting', 'depends on']):
                blocker_counts['Dependencies'] += 1
            elif any(k in text for k in ['resource', 'permission', 'access']):
                blocker_counts['Resources'] += 1
            elif any(k in text for k in ['meeting', 'approval', 'clarification', 'communication', 'design review']):
                blocker_counts['Communication'] += 1
            elif any(k in text for k in ['bug', 'error', 'broken', 'failing', 'crash', 'issue', 'problem', 'code', 'implementation']):
                blocker_counts['Technical'] += 1
            else:
                blocker_counts['Other'] += 1
        
        return blocker_counts

from integrations.services import WorkItemExtractor


class StandupView(LoginRequiredMixin, TemplateView):
    template_name = "standup/standup_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Allow demo mode without authentication
        if request.GET.get('demo') == 'true':
            return TemplateView.dispatch(self, request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            # Get today's date in Singapore timezone
            singapore_tz = pytz.timezone('Asia/Singapore')
            singapore_now = demo_now().astimezone(singapore_tz)
            today = singapore_now.date()
            
            try:
                team_member = TeamMember.objects.get(user=self.request.user)
                project = team_member.project
            except TeamMember.DoesNotExist:
                # For demo: Use the single demo project
                project = Project.objects.filter(status='active').first()
                if not project:
                    project = Project.objects.filter(name='MVP Team Health Project').first()
            
            if project:
                context['project'] = project
                
                # Check if user already has a standup session for today (don't create one)
                try:
                    standup_session = StandupSession.objects.get(
                        user=self.request.user,
                        project=project,
                        date=today
                    )
                    context['standup_session'] = standup_session
                    context['work_items'] = standup_session.work_item_refs.all()
                except StandupSession.DoesNotExist:
                    # No existing session - this is normal for new standups
                    context['standup_session'] = None
                    context['work_items'] = []
                
                # Get recent work items for context (from past sessions)
                recent_sessions = StandupSession.objects.filter(
                    project=project,
                    date__gte=today - timezone.timedelta(days=7)
                )
                
                if context['standup_session']:
                    recent_sessions = recent_sessions.exclude(id=context['standup_session'].id)
                
                recent_work_items = WorkItemReference.objects.filter(
                    standup_session__in=recent_sessions
                ).distinct('item_type', 'item_id')[:10]
                
                context['recent_work_items'] = recent_work_items
            else:
                messages.warning(self.request, "No project available for standup entries.")
                context['no_project'] = True
        
        return context


@login_required
@require_http_methods(["POST"])
def submit_standup(request):
    """Handle standup form submission with work item extraction."""
    try:
        # Get form data
        yesterday_work = request.POST.get('yesterday_work', '')
        today_plan = request.POST.get('today_plan', '')
        blockers = request.POST.get('blockers', '')
        # Mood selection removed - sentiment determined by BERT analysis only
        
        # Get or create today's standup session in Singapore timezone
        singapore_tz = pytz.timezone('Asia/Singapore')
        singapore_now = demo_now().astimezone(singapore_tz)
        today = singapore_now.date()
        try:
            team_member = TeamMember.objects.get(user=request.user)
            project = team_member.project
        except TeamMember.DoesNotExist:
            # For demo: Use the single demo project
            project = Project.objects.filter(status='active').first()
            if not project:
                project = Project.objects.filter(name='MVP Team Health Project').first()
            
            if not project:
                return JsonResponse({'success': False, 'error': 'No project available'}, status=400)
        
        standup_session, created = StandupSession.objects.get_or_create(
            user=request.user,
            project=project,
            date=today,
            defaults={'status': 'pending'}
        )
        
        # Update standup content
        standup_session.yesterday_work = yesterday_work
        standup_session.today_plan = today_plan
        standup_session.blockers = blockers
        standup_session.status = 'completed'
        
        # Process through BERT sentiment analysis
        current_sentiment_label = 'neutral'
        current_sentiment_score = 0.5
        
        try:
            from ai_processing.services import SentimentAnalysisService
            
            # Combine all standup text for BERT analysis
            combined_text = f"""
            Yesterday's work: {yesterday_work or ''}
            Today's plan: {today_plan or ''}
            Blockers: {blockers or ''}
            """.strip()
            
            if combined_text:
                sentiment_service = SentimentAnalysisService()
                bert_result = sentiment_service.analyse_sentiment(combined_text)
                
                if bert_result:
                    # Convert BERT sentiment label to numeric score
                    bert_to_score = {
                        'Very Positive': 0.9,
                        'Positive': 0.7,
                        'Neutral': 0.5,
                        'Negative': 0.3,
                        'Very Negative': 0.1
                    }
                    
                    bert_sentiment = bert_result.get('sentiment', 'Neutral')
                    bert_score = bert_to_score.get(bert_sentiment, 0.5)
                    
                    # Store for database
                    standup_session.sentiment_score = bert_score
                    standup_session.sentiment_label = bert_sentiment.lower().replace(' ', '_')
                    
                    # Store for AI context (use actual BERT results)
                    current_sentiment_label = bert_sentiment.lower().replace(' ', '_')
                    current_sentiment_score = bert_score
                    
                    # BERT analysis completed successfully
                
        except Exception as e:
            # BERT sentiment analysis failed
            # Fallback to neutral if BERT fails
            standup_session.sentiment_score = 0.5
            standup_session.sentiment_label = 'neutral'
        
        standup_session.save()
        
        # Extract and process work item references
        try:
            # Import here to allow for test mocking
            from integrations.services import GitHubService, JiraService
            
            github_service = GitHubService(
                access_token=getattr(settings, 'GITHUB_ACCESS_TOKEN', None),
                repository_name=getattr(settings, 'GITHUB_REPOSITORY', 'mock/repo'),
                use_mock_data=True,
                user=request.user  # Pass user for privacy checks
            )
            jira_service = JiraService(use_mock_data=True, user=request.user)
            
            extractor = WorkItemExtractor(
                github_service=github_service,
                jira_service=jira_service
            )
            
            work_items = extractor.process_standup_references(standup_session)
                
        except Exception as extraction_error:
            # Log the error but continue - don't break standup submission if work item extraction fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during work item extraction: {extraction_error}")
            work_items = []
        
        # Generate AI Strategic Analysis using the full AI processing pipeline
        try:
            from ai_processing.services import AIOrchestrationService
            from dashboard.models import WorkItemReference
            from datetime import timedelta
            
            # Build comprehensive context for strategic AI analysis
            end_date = today
            start_date = end_date - timedelta(days=7)  # Past week for context
            
            # Gather GitHub/Jira context from work item references
            refs = WorkItemReference.objects.filter(
                standup_session__project=project,
                standup_session__date__range=[start_date, end_date]
            ).select_related('standup_session__user')
            
            github_data = {
                'pull_requests': [],
                'issues': []
            }
            # Get mock sprint info from Jira service
            mock_sprint_info = jira_service.get_sprint_info()
            
            # Initialise with mock data from services
            jira_data = {
                'issues': [],
                'sprint_info': {
                    'completed_story_points': mock_sprint_info.get('completed_story_points', 15),
                    'total_story_points': mock_sprint_info.get('total_story_points', 30),
                    'team_velocity': mock_sprint_info.get('team_velocity', 28),
                    'goal': mock_sprint_info.get('goal', 'Complete user authentication system and resolve critical security issues')
                }
            }
            
            # Build GitHub/Jira context from actual work item references
            for r in refs:
                item_type = (r.item_type or '').lower()
                item_data = {
                    'id': r.item_id,
                    'title': r.title,
                    'status': getattr(r, 'status', 'open'),
                    'user': r.standup_session.user.username,
                    'date': str(r.standup_session.date)
                }
                
                if 'github_pr' in item_type or 'pr' in item_type:
                    item_data['ci'] = {'checks_passed': True, 'coverage': 0.85}
                    github_data['pull_requests'].append(item_data)
                elif 'github_issue' in item_type or 'issue' in item_type:
                    github_data['issues'].append(item_data)
                elif 'jira' in item_type or 'ticket' in item_type:
                    jira_data['issues'].append(item_data)
            
            # Add mock data if no real work items found to ensure rich analysis
            if not github_data['pull_requests'] and not github_data['issues'] and not jira_data['issues']:
                # Get mock data from services
                mock_jira_issues = jira_service.get_issues_for_user(request.user.email)
                if mock_jira_issues:
                    for issue in mock_jira_issues[:3]:  # Limit to 3 issues
                        jira_data['issues'].append({
                            'id': issue.get('key', 'UNKNOWN'),
                            'title': issue.get('summary', 'No title'),
                            'status': issue.get('status', 'open'),
                            'user': request.user.username,
                            'date': str(today)
                        })
                
                # Add some mock GitHub PRs using consistent pattern
                github_data['pull_requests'] = [
                    {
                        'id': 'PR-123',
                        'title': 'Implement OAuth 2.0 authentication flow',
                        'status': 'merged',
                        'user': request.user.username,
                        'date': str(today),
                        'ci': {'checks_passed': True, 'coverage': 0.87}
                    },
                    {
                        'id': 'PR-119',  
                        'title': 'Fix payment gateway integration timeout',
                        'status': 'open',
                        'user': request.user.username,
                        'date': str(today),
                        'ci': {'checks_passed': False, 'coverage': 0.82}
                    }
                ]
                
                # Add mock GitHub issues if still none
                if not github_data['issues']:
                    github_data['issues'] = [
                        {
                            'id': 'ISSUE-456',
                            'title': 'User session timeout handling', 
                            'status': 'in_progress',
                            'user': request.user.username,
                            'date': str(today)
                        }
                    ]
            
            # Gather sentiment context for team-wide analysis
            team_sessions = StandupSession.objects.filter(
                project=project,
                date__range=[start_date, end_date]
            ).select_related('user')
            
            sentiment_data = {
                'overall_sentiment': current_sentiment_label,
                'confidence': current_sentiment_score,
                'recent_updates': []
            }
            
            # Add current user's update with actual BERT results
            sentiment_data['recent_updates'].append({
                'user': request.user.username,
                'text': combined_text,
                'sentiment': current_sentiment_label,
                'confidence': current_sentiment_score,
                'date': str(today)
            })
            
            # Add recent team context for richer analysis
            for session in team_sessions[:10]:  # Last 10 team updates for context
                if session.user != request.user:  # Don't duplicate current user
                    session_text = f"{session.yesterday_work or ''} {session.today_plan or ''} {session.blockers or ''}".strip()
                    if session_text:
                        sentiment_data['recent_updates'].append({
                            'user': session.user.username,
                            'text': session_text,
                            'sentiment': session.sentiment_label or 'neutral',
                            'confidence': session.sentiment_score or 0.5,
                            'date': str(session.date)
                        })
            
            # Calculate overall team sentiment
            if sentiment_data['recent_updates']:
                scores = [update['confidence'] for update in sentiment_data['recent_updates']]
                avg_sentiment = sum(scores) / len(scores)
                sentiment_data['overall_sentiment'] = 'positive' if avg_sentiment >= 0.6 else 'neutral' if avg_sentiment >= 0.4 else 'negative'
                sentiment_data['confidence'] = avg_sentiment
            
            # Create comprehensive context for AI analysis
            ai_context = {
                'jira_data': jira_data,
                'github_data': github_data,
                'sentiment_data': sentiment_data,
                'user_info': {
                    'username': request.user.username,
                    'full_name': request.user.get_full_name() or request.user.username,
                    'first_name': request.user.first_name or request.user.username
                }
            }
            
            # Generate strategic AI analysis using the full pipeline
            ai_service = AIOrchestrationService()
            ai_results = ai_service.process_standup(
                text_update=combined_text,
                context=ai_context,
                user=request.user  # Pass user for privacy checks
            )
            
            # Store AI strategic analysis results
            if ai_results and 'summary' in ai_results:
                # The SummaryGenerationService returns a string directly
                summary_text = ai_results['summary']
                if summary_text and summary_text != "Summary generation failed":
                    standup_session.ai_summary = summary_text
                    standup_session.save()
                    # AI Strategic Analysis generated successfully
                else:
                    # AI Strategic Analysis failed or returned empty
                    pass
            
        except Exception as ai_error:
            # Log AI processing error but don't break standup submission
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during AI strategic analysis: {ai_error}")
            # AI Strategic Analysis failed
        
        # Create success message with work item summary
        if work_items:
            work_summary = ", ".join([item.display_name for item in work_items])
            messages.success(
                request, 
                f"Standup submitted successfully! Found work items: {work_summary}"
            )
        else:
            messages.success(request, "Standup submitted successfully!")
        
        
        # Handle AJAX vs normal form submission
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON response for AJAX requests
            return JsonResponse({
                'success': True,
                'message': "Standup submitted successfully!",
                'summary': standup_session.summary_text or '',
                'sentiment': standup_session.sentiment_score or 3.0
            })
        else:
            # Traditional form submission redirect
            return redirect('standup_form')
        
    except TeamMember.DoesNotExist:
        error_msg = "You need to be assigned to a project to submit standup entries."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        else:
            messages.error(request, error_msg)
            return redirect('standup_form')
    except Exception as e:
        error_msg = f"Error submitting standup: {str(e)}"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        else:
            messages.error(request, error_msg)
            return redirect('standup_form')


@login_required
@require_http_methods(["GET"])
def get_work_items_context(request):
    """API endpoint to get work items context for a project."""
    try:
        team_member = TeamMember.objects.get(user=request.user)
        project = team_member.project
        
        extractor = WorkItemExtractor()
        stats = extractor.get_project_work_items(project, days_back=30)
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_items': stats['total_items'],
                'by_type': stats['by_type'],
                'most_mentioned': [
                    {
                        'display_name': item['display_name'],
                        'title': item['title'],
                        'mention_count': item['mention_count'],
                        'item_type': item['work_item'].item_type,
                    }
                    for item in stats['most_mentioned']
                ]
            }
        })
        
    except TeamMember.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not assigned to a project'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def resolve_blocker(request, blocker_id):
    """Resolve a specific blocker."""
    try:
        blocker = Blocker.objects.get(id=blocker_id)
        
        # Check if user has permission to resolve this blocker
        # For now, allow the blocker owner or any team member in the same project
        user_team_member = None
        try:
            user_team_member = TeamMember.objects.get(user=request.user)
        except TeamMember.DoesNotExist:
            pass
        
        can_resolve = (
            blocker.standup_session.user == request.user or  # Blocker owner
            (user_team_member and user_team_member.project == blocker.standup_session.project)  # Same project
        )
        
        if not can_resolve:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to resolve this blocker'
            }, status=403)
        
        # Get resolution notes from request
        resolution_notes = request.POST.get('resolution_notes', '')
        
        # Resolve the blocker
        blocker.resolve(resolved_by_user=request.user, resolution_notes=resolution_notes)
        
        return JsonResponse({
            'success': True,
            'message': f'Blocker "{blocker.title}" has been resolved',
            'blocker_id': blocker.id,
            'resolved_at': blocker.resolved_at.isoformat() if blocker.resolved_at else None,
            'resolved_by': request.user.username
        })
        
    except Blocker.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Blocker not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def unresolve_blocker(request, blocker_id):
    """Mark a resolved blocker as active again."""
    try:
        blocker = Blocker.objects.get(id=blocker_id)
        
        # Check if user has permission to unresolve this blocker
        user_team_member = None
        try:
            user_team_member = TeamMember.objects.get(user=request.user)
        except TeamMember.DoesNotExist:
            pass
        
        can_unresolve = (
            blocker.standup_session.user == request.user or  # Blocker owner
            (user_team_member and user_team_member.project == blocker.standup_session.project)  # Same project
        )
        
        if not can_unresolve:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to unresolve this blocker'
            }, status=403)
        
        # Unresolve the blocker
        blocker.unresolve()
        
        return JsonResponse({
            'success': True,
            'message': f'Blocker "{blocker.title}" is now active again',
            'blocker_id': blocker.id
        })
        
    except Blocker.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Blocker not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def parse_blockers_from_text(request):
    """Parse blockers from standup text and create individual Blocker objects."""
    try:
        standup_session_id = request.POST.get('standup_session_id')
        blocker_text = request.POST.get('blocker_text', '')
        
        if not standup_session_id or not blocker_text.strip():
            return JsonResponse({
                'success': False,
                'error': 'Missing standup session ID or blocker text'
            })
        
        try:
            standup_session = StandupSession.objects.get(id=standup_session_id)
        except StandupSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Standup session not found'
            }, status=404)
        
        # Check permission
        if standup_session.user != request.user:
            try:
                user_team_member = TeamMember.objects.get(user=request.user)
                if user_team_member.project != standup_session.project:
                    return JsonResponse({
                        'success': False,
                        'error': 'You do not have permission to manage blockers for this session'
                    }, status=403)
            except TeamMember.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have permission to manage blockers for this session'
                }, status=403)
        
        # Parse individual blockers from text
        parsed_blockers = _parse_individual_blockers(blocker_text)
        
        created_blockers = []
        for blocker_data in parsed_blockers:
            blocker = Blocker.objects.create(
                standup_session=standup_session,
                title=blocker_data['title'],
                description=blocker_data['description'],
                category=blocker_data['category'],
                priority=blocker_data['priority']
            )
            created_blockers.append({
                'id': blocker.id,
                'title': blocker.title,
                'category': blocker.get_category_display(),
                'priority': blocker.get_priority_display()
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Created {len(created_blockers)} blocker(s)',
            'blockers': created_blockers
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def _parse_individual_blockers(blocker_text):
    """Parse blocker text into individual blocker objects with AI categorization."""
    blockers = []
    
    # Split on common delimiters (semicolon, bullet points, line breaks)
    import re
    
    # Split text by common separators
    blocker_parts = re.split(r'[;\n•\-]|\d+\.|\*', blocker_text)
    
    for part in blocker_parts:
        part = part.strip()
        if not part or len(part) < 10:  # Skip very short entries
            continue
        
        # Extract title (first sentence or up to 50 chars)
        title = part.split('.')[0][:50].strip()
        if not title:
            title = part[:50].strip()
        
        # Categorize based on keywords
        category = _categorize_blocker_text(part.lower())
        
        # Estimate priority based on keywords
        priority = _estimate_blocker_priority(part.lower())
        
        blockers.append({
            'title': title,
            'description': part,
            'category': category,
            'priority': priority
        })
    
    # If no individual blockers found, treat entire text as one blocker
    if not blockers:
        title = blocker_text.split('.')[0][:50].strip()
        if not title:
            title = blocker_text[:50].strip()
        
        blockers.append({
            'title': title,
            'description': blocker_text,
            'category': _categorize_blocker_text(blocker_text.lower()),
            'priority': _estimate_blocker_priority(blocker_text.lower())
        })
    
    return blockers


def _categorize_blocker_text(text):
    """Categorize blocker based on text content."""
    text = text.lower()
    
    if any(keyword in text for keyword in ['dependency', 'blocked by', 'waiting for', 'awaiting', 'depends on']):
        return 'dependencies'
    elif any(keyword in text for keyword in ['resource', 'permission', 'access', 'account', 'credentials', 'server']):
        return 'resources'
    elif any(keyword in text for keyword in ['meeting', 'approval', 'clarification', 'communication', 'design review', 'decision']):
        return 'communication'
    elif any(keyword in text for keyword in ['bug', 'error', 'broken', 'failing', 'crash', 'issue', 'problem', 'code', 'implementation']):
        return 'technical'
    else:
        return 'other'


def _estimate_blocker_priority(text):
    """Estimate blocker priority based on text content."""
    text = text.lower()
    
    if any(keyword in text for keyword in ['critical', 'urgent', 'blocker', 'emergency', 'asap', 'immediately']):
        return 'critical'
    elif any(keyword in text for keyword in ['high', 'important', 'major', 'significant', 'blocking']):
        return 'high'
    elif any(keyword in text for keyword in ['minor', 'small', 'low']):
        return 'low'
    else:
        return 'medium'
