import re
from datetime import datetime
from typing import List, Optional

from lxml.cssselect import CSSSelector
from lxml.etree import XPath

from src.parser.html_parser import ArticleBody, BaseParser, attribute
from src.parser.html_parser.utility import (
    extract_article_body_with_selector,
    generic_author_parsing,
    generic_date_parsing,
    generic_topic_parsing,
)


class APNewsParser(BaseParser):
    _author_selector: XPath = XPath(f"{CSSSelector('div.CardHeadline').path}/span/span[1]")

    @attribute
    def body(self) -> ArticleBody:
        return extract_article_body_with_selector(
            self.precomputed.doc,
            summary_selector="//div[@data-key = 'article']/p[1]",
            subheadline_selector="//div[@data-key = 'article']/h2",
            paragraph_selector="//div[@data-key = 'article']/p[position() > 1]",
            mode="xpath",
        )

    @attribute
    def authors(self) -> List[str]:
        # AP News does not have all the article's authors listed in the linked data.
        # Therefore, we try to parse the article's authors from the document.
        try:
            # Example: "By AUTHOR1, AUTHOR2 and AUTHOR3"
            author_string: str = self._author_selector(self.precomputed.doc)[0].text_content()
            author_string = author_string[3:]  # Strip "By "
        except IndexError:
            # Fallback to the generic author parsing from the linked data.
            return generic_author_parsing(self.precomputed.ld.get_value_by_key_path(["NewsArticle", "author"]))

        return re.split(r"\sand\s|,\s", author_string)

    @attribute
    def publishing_date(self) -> Optional[datetime]:
        return generic_date_parsing(self.precomputed.ld.get_value_by_key_path(["NewsArticle", "datePublished"]))

    @attribute
    def title(self) -> Optional[str]:
        title: str = self.precomputed.ld.get_value_by_key_path(["NewsArticle", "headline"])
        return title

    @attribute
    def topics(self) -> List[str]:
        return generic_topic_parsing(self.precomputed.meta.get("keywords"))