from app.core.config import settings


class DevToolsService:
    def describe_capabilities(self) -> str:
        capabilities = []
        if settings.gitlab_base_url and settings.gitlab_token:
            capabilities.append("GitLab API is configured.")
        else:
            capabilities.append("GitLab API is not configured yet.")

        if settings.jira_base_url and settings.jira_api_token:
            capabilities.append("Jira API is configured.")
        else:
            capabilities.append("Jira API is not configured yet.")

        if settings.confluence_base_url and settings.confluence_api_token:
            capabilities.append("Confluence API is configured.")
        else:
            capabilities.append("Confluence API is not configured yet.")

        return "\n".join(capabilities)


dev_tools_service = DevToolsService()
