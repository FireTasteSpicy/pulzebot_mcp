"""
Consolidated integration services for external platforms like GitHub and Jira.
Contains both real API integrations and mock data implementations.
Consolidated from multiple service files for better maintainability.
"""
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings

from github import Github
# Uncomment for real Jira integration:
# from jira import JIRA
# import requests
# from requests.auth import HTTPBasicAuth

# Consolidated utility functions (from utils.py)
def find_ticket_ids_in_text(text):
    """Find all Jira ticket IDs in a given string."""
    pattern = r'\b[A-Z]+-\d+\b'
    return re.findall(pattern, text)

def find_issue_numbers_in_text(text):
    """Find all GitHub issue numbers in a given string."""
    pattern = r'#(\d+)'
    return [int(num) for num in re.findall(pattern, text)]

def parse_github_url(url: str) -> tuple[str, str]:
    """Parse a GitHub URL to extract owner and repository name."""
    pattern = r'https://github\.com/([^/]+)/([^/]+)/?$'
    match = re.match(pattern, url)
    
    if not match:
        raise ValueError(f"Invalid GitHub URL format: {url}")
    
    return match.group(1), match.group(2)


class GitHubService:
    """Service for GitHub API integration with mock data fallback."""
    
    def __init__(self, access_token: str = None, repository_name: str = None, use_mock_data: bool = True, user=None):
        self.use_mock_data = use_mock_data
        self.repository_name = repository_name or "mock/repo"
        self.user = user
        
        # Real GitHub connection (commented out for development)
        if not use_mock_data and access_token:
            self.github = Github(access_token)
            self.repository = self.github.get_repo(repository_name)
        else:
            self.github = None
            self.repository = None

    def _check_external_integration_consent(self):
        """Check if user has consented to external integrations."""
        if not self.user:
            return True  # Allow if no user context (demo/testing)
        
        try:
            from user_settings.models import UserSettings
            settings, created = UserSettings.objects.get_or_create(user=self.user)
            return settings.allow_external_integrations
        except Exception as e:
            print(f"Error checking external integration consent: {e}")
            return False

    def get_pull_requests(self):
        """Get pull requests from GitHub repository with privacy controls."""
        # Check privacy consent first
        if not self._check_external_integration_consent():
            return []
        
        if self.use_mock_data or self.repository is None:
            return self._get_mock_pull_requests()
        
        # Real GitHub implementation (commented out):
        # return self.repository.get_pulls()

    def get_pull_request_details(self, pr_number: int) -> Dict[str, Any]:
        """Get detailed information about a specific pull request with privacy controls."""
        # Check privacy consent first
        if not self._check_external_integration_consent():
            return {}
            
        if self.use_mock_data or self.repository is None:
            return self._get_mock_pull_request_details(pr_number)
        
        # Real GitHub implementation (commented out):
        # try:
        #     pr = self.repository.get_pull(pr_number)
        #     return {
        #         "number": pr.number,
        #         "title": pr.title,
        #         "state": pr.state,
        #         "author": pr.user.login,
        #         "created_at": pr.created_at.isoformat(),
        #         "updated_at": pr.updated_at.isoformat(),
        #         "status_checks": self._get_status_checks(pr),
        #         "reviews": self._get_reviews(pr),
        #         "commits": pr.commits,
        #         "additions": pr.additions,
        #         "deletions": pr.deletions,
        #         "changed_files": pr.changed_files
        #     }
        # except Exception:
        #     return self._get_mock_pull_request_details(pr_number)

    def get_issue_details(self, issue_number: int) -> Dict[str, Any]:
        """Get detailed information about a specific GitHub issue."""
        if self.use_mock_data or self.repository is None:
            return self._get_mock_issue_details(issue_number)
        
        # Real GitHub implementation (commented out):
        # try:
        #     issue = self.repository.get_issue(issue_number)
        #     return {
        #         "number": issue.number,
        #         "title": issue.title,
        #         "state": issue.state,
        #         "author": issue.user.login,
        #         "created_at": issue.created_at.isoformat(),
        #         "updated_at": issue.updated_at.isoformat(),
        #         "html_url": issue.html_url,
        #         "labels": [label.name for label in issue.labels],
        #         "assignees": [assignee.login for assignee in issue.assignees],
        #         "milestone": issue.milestone.title if issue.milestone else None,
        #         "comments": issue.comments,
        #         "body": issue.body[:500] if issue.body else "",  # Truncate body
        #     }
        # except Exception as e:
        #     return self._get_mock_issue_details(issue_number)

    def _get_status_checks(self, pr) -> Dict[str, str]:
        """Get status checks for a pull request."""
        try:
            commit = pr.get_commits().reversed[0]
            statuses = commit.get_statuses()
            return {status.context: status.state for status in statuses}
        except:
            return {}

    def _get_reviews(self, pr) -> List[Dict[str, Any]]:
        """Get reviews for a pull request."""
        try:
            reviews = pr.get_reviews()
            return [{
                "user": review.user.login,
                "state": review.state,
                "submitted_at": review.submitted_at.isoformat()
            } for review in reviews]
        except:
            return []

    def _get_mock_pull_requests(self):
        """Return mock pull request data."""
        mock_prs = []
        for i in range(1, 4):
            mock_prs.append({
                "number": i,
                "title": f"Mock PR #{i}: Feature implementation",
                "state": "open" if i < 3 else "closed",
                "author": f"developer{i}",
                "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_mock": True
            })
        return mock_prs

    def _get_mock_pull_request_details(self, pr_number: int) -> Dict[str, Any]:
        """Return mock pull request details."""
        return {
            "number": pr_number,
            "title": f"Mock PR #{pr_number}: Feature implementation",
            "state": "open" if pr_number < 3 else "closed",
            "author": f"developer{pr_number}",
            "created_at": (datetime.now() - timedelta(days=pr_number)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status_checks": {"ci/build": "success", "ci/test": "pending"},
            "reviews": [
                {
                    "user": "reviewer1",
                    "state": "approved",
                    "submitted_at": datetime.now().isoformat()
                }
            ],
            "commits": 5,
            "additions": 150,
            "deletions": 30,
            "changed_files": 8,
            "is_mock": True
        }

    def _get_mock_issue_details(self, issue_number: int) -> Dict[str, Any]:
        """Return mock issue details."""
        return {
            "number": issue_number,
            "title": f"Mock Issue #{issue_number}: Sample GitHub Issue",
            "state": "open" if issue_number % 2 == 1 else "closed",
            "author": f"user{issue_number}",
            "created_at": (datetime.now() - timedelta(days=issue_number * 2)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "html_url": f"https://github.com/{self.repository_name}/issues/{issue_number}",
            "labels": ["bug", "help-wanted"] if issue_number % 2 == 1 else ["enhancement", "feature"],
            "assignees": [f"assignee{issue_number}"],
            "milestone": f"Sprint {issue_number // 5 + 1}" if issue_number > 0 else None,
            "comments": issue_number % 5,
            "body": f"This is a mock issue #{issue_number} for development and testing purposes. It contains sample data to simulate real GitHub issues.",
            "is_mock": True
        }


class JiraService:
    """Service for Jira API integration with mock data fallback."""
    
    def __init__(self, use_mock_data: bool = True, user=None):
        self.use_mock_data = use_mock_data
        self.user = user
        
        # Real Jira connection (commented out for development)
        # Uncomment these lines for real Jira integration:
        # if not use_mock_data:
        #     self.jira_url = os.getenv('JIRA_URL')
        #     self.jira_username = os.getenv('JIRA_USERNAME') 
        #     self.jira_api_token = os.getenv('JIRA_API_TOKEN')
        #     self.jira = JIRA(
        #         server=self.jira_url,
        #         basic_auth=(self.jira_username, self.jira_api_token)
        #     )
        # else:
        #     self.jira = None
        
        self.jira = None  # Always use mock data for now

    def _check_external_integration_consent(self):
        """Check if user has consented to external integrations."""
        if not self.user:
            return True  # Allow if no user context (demo/testing)
        
        try:
            from user_settings.models import UserSettings
            settings, created = UserSettings.objects.get_or_create(user=self.user)
            return settings.allow_external_integrations
        except Exception as e:
            print(f"Error checking external integration consent: {e}")
            return False

    def get_issues_for_user(self, user_email: str, project_key: str = None) -> List[Dict[str, Any]]:
        """Get Jira issues assigned to a specific user with privacy controls."""
        # Check privacy consent first
        if not self._check_external_integration_consent():
            return []
            
        if self.use_mock_data or self.jira is None:
            return self._get_mock_user_issues(user_email, project_key)
        
        # Real Jira implementation (commented out):
        # try:
        #     jql = f'assignee = "{user_email}"'
        #     if project_key:
        #         jql += f' AND project = "{project_key}"'
        #     jql += ' AND status != "Done" ORDER BY priority DESC, updated DESC'
        #     
        #     issues = self.jira.search_issues(jql, maxResults=50)
        #     return [self._format_jira_issue(issue) for issue in issues]
        # except Exception as e:
        #     print(f"Error fetching Jira issues: {e}")
        #     return self._get_mock_user_issues(user_email, project_key)

    def get_sprint_info(self, board_id: int = None) -> Dict[str, Any]:
        """Get current sprint information with privacy controls."""
        # Check privacy consent first
        if not self._check_external_integration_consent():
            return {}
            
        if self.use_mock_data or self.jira is None:
            return self._get_mock_sprint_info()
        
        # Real Jira implementation (commented out):
        # try:
        #     if board_id:
        #         sprints = self.jira.sprints(board_id, state='active')
        #         if sprints:
        #             active_sprint = sprints[0]
        #             sprint_issues = self.jira.search_issues(
        #                 f'sprint = {active_sprint.id}',
        #                 expand='changelog'
        #             )
        #             return self._format_sprint_info(active_sprint, sprint_issues)
        #     return self._get_mock_sprint_info()
        # except Exception as e:
        #     print(f"Error fetching sprint info: {e}")
        #     return self._get_mock_sprint_info()

    def get_project_metrics(self, project_key: str) -> Dict[str, Any]:
        """Get project-level metrics and KPIs."""
        if self.use_mock_data or self.jira is None:
            return self._get_mock_project_metrics(project_key)
        
        # Real Jira implementation (commented out):
        # try:
        #     # Get project statistics
        #     project = self.jira.project(project_key)
        #     
        #     # Calculate metrics from recent activity
        #     recent_issues = self.jira.search_issues(
        #         f'project = "{project_key}" AND updated >= -30d',
        #         maxResults=1000
        #     )
        #     
        #     return self._calculate_project_metrics(project, recent_issues)
        # except Exception as e:
        #     print(f"Error fetching project metrics: {e}")
        #     return self._get_mock_project_metrics(project_key)

    def _get_mock_user_issues(self, user_email: str, project_key: str = None) -> List[Dict[str, Any]]:
        """Generate mock Jira issues for development using actual team member assignments."""
        base_issues = [
            {
                "key": "DEV-123",
                "summary": "Implement OAuth2 authentication system",
                "status": "In Progress",
                "assignee": "alice_dev@example.com",
                "priority": "High",
                "story_points": 8,
                "blockers": ["Waiting for security team review"],
                "epic": "User Authentication Epic",
                "labels": ["backend", "security", "authentication"],
                "created": (datetime.now() - timedelta(days=5)).isoformat(),
                "updated": (datetime.now() - timedelta(hours=2)).isoformat(),
                "progress": 60
            },
            {
                "key": "DEV-124", 
                "summary": "Fix user session timeout bug",
                "status": "Code Review",
                "assignee": "bob_lead@example.com",
                "priority": "Medium",
                "story_points": 3,
                "blockers": [],
                "epic": "Bug Fixes Sprint",
                "labels": ["frontend", "bug", "session"],
                "created": (datetime.now() - timedelta(days=3)).isoformat(),
                "updated": (datetime.now() - timedelta(hours=6)).isoformat(),
                "progress": 85
            },
            {
                "key": "DEV-125",
                "summary": "Update API documentation for v2.0",
                "status": "To Do",
                "assignee": "carol_qa@example.com",
                "priority": "Low",
                "story_points": 2,
                "blockers": ["Waiting for API finalization"],
                "epic": "Documentation Update",
                "labels": ["documentation", "api"],
                "created": (datetime.now() - timedelta(days=1)).isoformat(),
                "updated": (datetime.now() - timedelta(hours=12)).isoformat(),
                "progress": 10
            },
            {
                "key": "DEV-126",
                "summary": "Design new user dashboard UI",
                "status": "In Progress",
                "assignee": "david_design@example.com",
                "priority": "Medium",
                "story_points": 5,
                "blockers": [],
                "epic": "UI/UX Improvements",
                "labels": ["frontend", "design", "ui"],
                "created": (datetime.now() - timedelta(days=4)).isoformat(),
                "updated": (datetime.now() - timedelta(hours=8)).isoformat(),
                "progress": 40
            },
            {
                "key": "DEV-127",
                "summary": "Implement real-time notifications",
                "status": "Code Review",
                "assignee": "eve_dev@example.com",
                "priority": "High",
                "story_points": 6,
                "blockers": [],
                "epic": "Real-time Features",
                "labels": ["backend", "websockets", "notifications"],
                "created": (datetime.now() - timedelta(days=6)).isoformat(),
                "updated": (datetime.now() - timedelta(hours=4)).isoformat(),
                "progress": 75
            }
        ]
        
        # Filter by user if specified
        if user_email:
            return [issue for issue in base_issues if issue["assignee"] == user_email]
        
        return base_issues

    def _get_mock_sprint_info(self) -> Dict[str, Any]:
        """Generate mock sprint information using actual team members."""
        return {
            "name": "Sprint 15 - Authentication & Security",
            "goal": "Complete user authentication system and resolve critical security issues",
            "state": "active",
            "start_date": (datetime.now() - timedelta(days=8)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=6)).isoformat(),
            "total_story_points": 30,
            "completed_story_points": 15,
            "remaining_story_points": 15,
            "team_velocity": 28,
            "burndown_data": [
                {"day": 1, "remaining": 30, "ideal": 28},
                {"day": 2, "remaining": 28, "ideal": 26},
                {"day": 3, "remaining": 24, "ideal": 24},
                {"day": 4, "remaining": 22, "ideal": 22},
                {"day": 5, "remaining": 18, "ideal": 20},
                {"day": 6, "remaining": 16, "ideal": 18},
                {"day": 7, "remaining": 15, "ideal": 16},
                {"day": 8, "remaining": 15, "ideal": 14}
            ],
            "team_members": [
                {"name": "Alice Developer", "email": "alice_dev@example.com", "capacity": 8},
                {"name": "Bob Lead", "email": "bob_lead@example.com", "capacity": 8},
                {"name": "Carol QA", "email": "carol_qa@example.com", "capacity": 8},
                {"name": "David Designer", "email": "david_design@example.com", "capacity": 8},
                {"name": "Eve Developer", "email": "eve_dev@example.com", "capacity": 8},
                {"name": "Manager", "email": "manager@pulzebot.com", "capacity": 6},
                {"name": "User", "email": "user@pulzebot.com", "capacity": 8},
                {"name": "Admin", "email": "admin@example.com", "capacity": 4}
            ]
        }

    def _get_mock_project_metrics(self, project_key: str) -> Dict[str, Any]:
        """Generate mock project metrics."""
        return {
            "project_key": project_key,
            "total_issues": 156,
            "open_issues": 23,
            "in_progress": 8,
            "done_this_month": 34,
            "average_cycle_time": 4.2,  # days
            "defect_rate": 0.12,  # 12%
            "team_satisfaction": 4.1,  # out of 5
            "velocity_trend": "increasing",
            "top_blockers": [
                "External API dependencies",
                "Code review bottleneck", 
                "Environment setup issues"
            ],
            "recent_deployments": [
                {
                    "version": "v2.3.1",
                    "date": (datetime.now() - timedelta(days=3)).isoformat(),
                    "issues_resolved": 12,
                    "status": "successful"
                },
                {
                    "version": "v2.3.0", 
                    "date": (datetime.now() - timedelta(days=10)).isoformat(),
                    "issues_resolved": 18,
                    "status": "successful"
                }
            ]
        }

    # Real Jira helper methods (commented out for development):
    # def _format_jira_issue(self, issue) -> Dict[str, Any]:
    #     """Format a Jira issue object into our standard format."""
    #     return {
    #         "key": issue.key,
    #         "summary": issue.fields.summary,
    #         "status": issue.fields.status.name,
    #         "assignee": issue.fields.assignee.emailAddress if issue.fields.assignee else None,
    #         "priority": issue.fields.priority.name if issue.fields.priority else "Medium",
    #         "story_points": getattr(issue.fields, 'customfield_10016', 0),  # Story points field
    #         "epic": getattr(issue.fields, 'customfield_10014', None),  # Epic link field
    #         "labels": issue.fields.labels,
    #         "created": issue.fields.created,
    #         "updated": issue.fields.updated,
    #         "blockers": self._extract_blockers(issue)
    #     }
    #
    # def _format_sprint_info(self, sprint, issues) -> Dict[str, Any]:
    #     """Format sprint information from Jira objects."""
    #     total_points = sum(getattr(issue.fields, 'customfield_10016', 0) for issue in issues)
    #     completed_points = sum(
    #         getattr(issue.fields, 'customfield_10016', 0) 
    #         for issue in issues 
    #         if issue.fields.status.name in ['Done', 'Closed']
    #     )
    #     
    #     return {
    #         "name": sprint.name,
    #         "goal": getattr(sprint, 'goal', ''),
    #         "state": sprint.state,
    #         "start_date": sprint.startDate,
    #         "end_date": sprint.endDate,
    #         "total_story_points": total_points,
    #         "completed_story_points": completed_points,
    #         "remaining_story_points": total_points - completed_points
    #     }
    #
    # def _extract_blockers(self, issue) -> List[str]:
    #     """Extract blocker information from issue links."""
    #     blockers = []
    #     if hasattr(issue.fields, 'issuelinks'):
    #         for link in issue.fields.issuelinks:
    #             if link.type.name == 'Blocks' and hasattr(link, 'inwardIssue'):
    #                 blockers.append(f"{link.inwardIssue.key}: {link.inwardIssue.fields.summary}")
    #     return blockers


class IntegrationOrchestrationService:
    """Orchestrates data from multiple external services."""
    
    def __init__(self, use_mock_data: bool = True):
        self.use_mock_data = use_mock_data
        self.jira_service = JiraService(use_mock_data=use_mock_data)
    
    def get_unified_context(self, 
                          jira_ticket_ids: List[str] = None,
                          github_repo: str = None, 
                          github_pr_numbers: List[int] = None,
                          user_email: str = None) -> Dict[str, Any]:
        """Get unified context from all integrated services."""
        
        context = {
            "jira_data": {},
            "github_data": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Get Jira data
        try:
            if jira_ticket_ids:
                # Get all issues and filter by the requested ticket IDs
                all_issues = self.jira_service.get_issues_for_user("")  # Get all issues
                context["jira_data"]["issues"] = [issue for issue in all_issues if issue["key"] in jira_ticket_ids]
            else:
                context["jira_data"]["issues"] = self.jira_service.get_issues_for_user(
                    user_email or "alice_dev@example.com"
                )
            
            context["jira_data"]["sprint_info"] = self.jira_service.get_sprint_info()
            context["jira_data"]["project_metrics"] = self.jira_service.get_project_metrics("DEV")
            
        except Exception as e:
            print(f"Error fetching Jira data: {e}")
            context["jira_data"] = {"issues": [], "sprint_info": {}, "error": str(e)}
        
        # Get GitHub data with actual team members
        try:
            if github_repo and github_pr_numbers:
                # Mock GitHub data using actual team members
                context["github_data"]["pull_requests"] = [
                    {
                        "number": 42,
                        "title": "feat: Add OAuth2 authentication endpoints", 
                        "state": "open",
                        "author": "alice_dev",
                        "status_checks": {
                            "ci": "pending",
                            "tests": "passed", 
                            "security_scan": "failed"
                        },
                        "reviews": [
                            {"user": "bob_lead", "state": "approved", "submitted_at": datetime.now().isoformat()},
                            {"user": "carol_qa", "state": "changes_requested", "submitted_at": (datetime.now() - timedelta(hours=2)).isoformat()}
                        ],
                        "assignees": ["alice_dev"],
                        "labels": ["enhancement", "authentication", "backend"],
                        "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
                        "updated_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                        "additions": 156,
                        "deletions": 23,
                        "changed_files": 8
                    },
                    {
                        "number": 43,
                        "title": "fix: Resolve session timeout issues", 
                        "state": "merged",
                        "author": "bob_lead",
                        "status_checks": {
                            "ci": "passed",
                            "tests": "passed", 
                            "security_scan": "passed"
                        },
                        "reviews": [
                            {"user": "alice_dev", "state": "approved", "submitted_at": datetime.now().isoformat()},
                            {"user": "eve_dev", "state": "approved", "submitted_at": (datetime.now() - timedelta(hours=4)).isoformat()}
                        ],
                        "assignees": ["bob_lead"],
                        "labels": ["bug", "frontend", "session"],
                        "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
                        "updated_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                        "additions": 45,
                        "deletions": 12,
                        "changed_files": 3
                    },
                    {
                        "number": 44,
                        "title": "docs: Update API documentation for v2.0", 
                        "state": "draft",
                        "author": "carol_qa",
                        "status_checks": {
                            "ci": "not_run",
                            "tests": "not_run", 
                            "security_scan": "not_run"
                        },
                        "reviews": [],
                        "assignees": ["carol_qa", "david_design"],
                        "labels": ["documentation", "api"],
                        "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                        "updated_at": (datetime.now() - timedelta(hours=12)).isoformat(),
                        "additions": 89,
                        "deletions": 5,
                        "changed_files": 6
                    }
                ]
            else:
                context["github_data"]["pull_requests"] = []
                
        except Exception as e:
            print(f"Error fetching GitHub data: {e}")
            context["github_data"] = {"pull_requests": [], "error": str(e)}
        
        return context

    def get_team_productivity_metrics(self, team_emails: List[str], days: int = 30) -> Dict[str, Any]:
        """Get team productivity metrics across all platforms."""
        metrics = {
            "team_size": len(team_emails),
            "period_days": days,
            "jira_metrics": {},
            "github_metrics": {},
            "combined_metrics": {}
        }
        
        # Aggregate Jira metrics
        all_issues = []
        for email in team_emails:
            user_issues = self.jira_service.get_issues_for_user(email)
            all_issues.extend(user_issues)
        
        metrics["jira_metrics"] = {
            "total_issues": len(all_issues),
            "completed_issues": len([i for i in all_issues if i["status"] == "Done"]),
            "in_progress": len([i for i in all_issues if i["status"] == "In Progress"]),
            "total_story_points": sum(i["story_points"] for i in all_issues),
            "average_cycle_time": 4.2,  # Mock data
        }
        
        # Mock GitHub metrics
        metrics["github_metrics"] = {
            "pull_requests_opened": 15,
            "pull_requests_merged": 12,
            "code_reviews_completed": 23,
            "commits": 156
        }
        
        # Combined productivity score
        metrics["combined_metrics"] = {
            "productivity_score": 8.2,  # out of 10
            "team_velocity": metrics["jira_metrics"]["total_story_points"],
            "collaboration_index": 7.8,
            "quality_score": 8.5
        }
        
        return metrics


class GitHubIntegrationService:
    """Service for GitHub integration operations."""
    
    def __init__(self, integration):
        from .models import ExternalIntegration
        self.integration = integration
        self.api_key = integration.api_key if hasattr(integration, 'api_key') else None
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PulzeBot-Integration'
        }
        if self.api_key:
            headers['Authorization'] = f'token {self.api_key}'
        return headers
        
    def authenticate_with_token(self) -> bool:
        """Authenticate with GitHub using token."""
        if not self.api_key:
            return False
        try:
            github = Github(self.api_key)
            # Test authentication by getting user info
            user = github.get_user()
            return True
        except Exception:
            return False
    
    def fetch_repositories(self) -> List[Dict[str, Any]]:
        """Fetch repositories from GitHub."""
        if not self.api_key:
            raise Exception("No API key configured")
        
        try:
            github = Github(self.api_key)
            user = github.get_user()
            repos = []
            
            for repo in user.get_repos():
                repos.append({
                    'full_name': repo.full_name,
                    'name': repo.name,
                    'description': repo.description or '',
                    'private': repo.private,
                    'default_branch': repo.default_branch,
                    'language': repo.language or '',
                    'stars_count': repo.stargazers_count,
                    'forks_count': repo.forks_count,
                })
                
            return repos
        except Exception as e:
            raise Exception(f"Failed to fetch repositories: {str(e)}")
    
    def fetch_issues(self, repository_name: str) -> List[Dict[str, Any]]:
        """Fetch issues from a GitHub repository."""
        if not self.api_key:
            raise Exception("No API key configured")
        
        try:
            github = Github(self.api_key)
            repo = github.get_repo(repository_name)
            issues = []
            
            for issue in repo.get_issues(state='all'):
                if not issue.pull_request:  # Exclude pull requests
                    issues.append({
                        'external_id': f"ISSUE-{issue.number}",
                        'title': issue.title,
                        'description': issue.body or '',
                        'status': 'open' if issue.state == 'open' else 'closed',
                        'assignee': issue.assignee.login if issue.assignee else '',
                        'reporter': issue.user.login,
                        'labels': [label.name for label in issue.labels],
                        'external_url': issue.html_url,
                        'created_at_source': issue.created_at,
                        'updated_at_source': issue.updated_at,
                    })
                    
            return issues
        except Exception as e:
            raise Exception(f"Failed to fetch issues: {str(e)}")
    
    def fetch_pull_requests(self, repository_name: str) -> List[Dict[str, Any]]:
        """Fetch pull requests from a GitHub repository."""
        if not self.api_key:
            raise Exception("No API key configured")
        
        try:
            github = Github(self.api_key)
            repo = github.get_repo(repository_name)
            prs = []
            
            for pr in repo.get_pulls(state='all'):
                prs.append({
                    'external_id': f"PR-{pr.number}",
                    'title': pr.title,
                    'description': pr.body or '',
                    'status': 'open' if pr.state == 'open' else 'closed',
                    'assignee': pr.assignee.login if pr.assignee else '',
                    'reporter': pr.user.login,
                    'labels': [label.name for label in pr.labels],
                    'external_url': pr.html_url,
                    'created_at_source': pr.created_at,
                    'updated_at_source': pr.updated_at,
                })
                
            return prs
        except Exception as e:
            raise Exception(f"Failed to fetch pull requests: {str(e)}")


class WorkItemSyncService:
    """Service for synchronizing work items from external platforms."""
    
    def __init__(self, integration):
        from .models import ExternalIntegration
        self.integration = integration
        
    def sync_work_items(self) -> Dict[str, int]:
        """Sync work items from external platform."""
        from .models import WorkItem, GitHubRepository
        
        created_count = 0
        updated_count = 0
        
        if self.integration.platform == 'github':
            github_service = GitHubIntegrationService(self.integration)
            
            # Get repositories for this integration
            repos = GitHubRepository.objects.filter(integration__pk=self.integration.pk)
            
            for repo in repos:
                # Fetch and sync issues
                try:
                    issues = github_service.fetch_issues(repo.full_name)
                    for issue_data in issues:
                        work_item, created = WorkItem.objects.get_or_create(
                            integration=self.integration,
                            external_id=issue_data['external_id'],
                            defaults={
                                'item_type': 'issue',
                                'title': issue_data['title'],
                                'description': issue_data['description'],
                                'status': issue_data['status'],
                                'assignee': issue_data['assignee'],
                                'reporter': issue_data['reporter'],
                                'labels': issue_data['labels'],
                                'repository': repo,
                                'external_url': issue_data['external_url'],
                                'created_at_source': issue_data['created_at_source'],
                                'updated_at_source': issue_data['updated_at_source'],
                            }
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            # Update existing item
                            for field, value in issue_data.items():
                                if field != 'external_id':
                                    setattr(work_item, field, value)
                            work_item.save()
                            updated_count += 1
                            
                except Exception:
                    # Skip repositories that fail
                    continue
                
                # Fetch and sync pull requests
                try:
                    prs = github_service.fetch_pull_requests(repo.full_name)
                    for pr_data in prs:
                        work_item, created = WorkItem.objects.get_or_create(
                            integration=self.integration,
                            external_id=pr_data['external_id'],
                            defaults={
                                'item_type': 'pull_request',
                                'title': pr_data['title'],
                                'description': pr_data['description'],
                                'status': pr_data['status'],
                                'assignee': pr_data['assignee'],
                                'reporter': pr_data['reporter'],
                                'labels': pr_data['labels'],
                                'repository': repo,
                                'external_url': pr_data['external_url'],
                                'created_at_source': pr_data['created_at_source'],
                                'updated_at_source': pr_data['updated_at_source'],
                            }
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            # Update existing item
                            for field, value in pr_data.items():
                                if field != 'external_id':
                                    setattr(work_item, field, value)
                            work_item.save()
                            updated_count += 1
                            
                except Exception:
                    # Skip repositories that fail
                    continue
        
        return {
            'created': created_count,
            'updated': updated_count,
        }


# Consolidated WorkItemExtractor class (from work_item_extractor.py)
class WorkItemExtractor:
    """Service for extracting and processing work item references from standup text."""
    
    # Regex patterns for different work item types
    PATTERNS = {
        'github_pr': [
            r'\bPR\s*#?(\d+)',  # PR #123, PR123
            r'\bpull\s+request\s*#?(\d+)',  # pull request #123
            r'#(\d+)(?:\s+pr\b)',  # #123 pr
        ],
        'github_issue': [
            r'\bissue\s*#?(\d+)',  # issue #123, issue123
            r'\bbug\s*#?(\d+)',  # bug #123
            r'\bticket\s*#?(\d+)',  # ticket #123
        ],
        'jira_ticket': [
            r'\b([A-Z]{2,10}-\d+)\b',  # ABC-123, PROJ-456
        ],
        'branch': [
            r'(?:branch|feature|hotfix|bugfix)[:\/\s]+([a-zA-Z0-9\-_\/\.]+)',
        ]
    }
    
    def __init__(self, github_service=None, jira_service=None):
        """Initialise with optional external service instances."""
        self.github_service = github_service
        self.jira_service = jira_service
    
    def extract_work_references(self, text: str) -> Dict[str, List[str]]:
        """Extract all work item references from the given text."""
        references = {}
        
        # Extract GitHub PRs
        pr_numbers = set()
        for pattern in self.PATTERNS['github_pr']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            pr_numbers.update(matches)
        
        if pr_numbers:
            references['github_pr'] = sorted(list(pr_numbers))
        
        # Extract GitHub Issues
        issue_numbers = set()
        for pattern in self.PATTERNS['github_issue']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            issue_numbers.update(matches)
        
        if issue_numbers:
            references['github_issue'] = sorted(list(issue_numbers))
        
        # Extract Jira tickets
        jira_matches = re.findall(self.PATTERNS['jira_ticket'][0], text)
        if jira_matches:
            references['jira_ticket'] = jira_matches
        
        # Extract branch references
        branch_matches = []
        for pattern in self.PATTERNS['branch']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            branch_matches.extend(matches)
        
        if branch_matches:
            references['branch'] = branch_matches
        
        return references
