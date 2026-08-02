from dataclasses import dataclass
from typing import Optional

@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: str
    url: str
    paper_type: str  # 'classic' or 'latest'
    summary: Optional[str] = None      # 1. 摘要
    problem: Optional[str] = None      # 2. 問題
    method: Optional[str] = None       # 3. 方法
    conclusion: Optional[str] = None   # 4. 結論
    formatted_post: Optional[str] = None
    is_published: bool = False
    published_at: Optional[str] = None
    created_at: Optional[str] = None
    id: Optional[int] = None
