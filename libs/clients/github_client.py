from typing import List


class GithubClient:
    def get_files_content(self, file_list: List[str], repo_full_name: str) -> List[str]:
        raise NotImplementedError
