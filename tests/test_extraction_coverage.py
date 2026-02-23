"""
Tests for extract_name_role_pairs() extraction coverage improvements.
Covers: CSS class-based (Strategy 0), h6/strong headings, grid layouts,
nested roles, expanded ROLE_KEYWORDS.
"""

from bs4 import BeautifulSoup
from deep_crawl import extract_name_role_pairs, ROLE_KEYWORDS


# ── Test HTML Snippets ─────────────────────────────


HTML_STANDARD_CARDS = """
<div>
  <div class="card">
    <h3>Jane Smith</h3>
    <p>Managing Partner</p>
  </div>
  <div class="card">
    <h3>John Doe</h3>
    <p>General Partner</p>
  </div>
</div>
"""

HTML_CSS_CLASS_BASED = """
<div>
  <div class="team-member">
    <h4>Alice Johnson</h4>
    <span>Venture Partner</span>
  </div>
  <div class="team-member">
    <h4>Bob Williams</h4>
    <span>Principal</span>
  </div>
  <div class="team-member">
    <h4>Carol Davis</h4>
    <span>Investor Relations</span>
  </div>
</div>
"""

HTML_GRID_LAYOUT = """
<div class="team-grid">
  <div>
    <h5>David Brown</h5>
    <p>Senior Associate</p>
  </div>
  <div>
    <h5>Emily Wilson</h5>
    <p>Operating Partner</p>
  </div>
  <div>
    <h5>Frank Miller</h5>
    <p>Analyst</p>
  </div>
  <div>
    <h5>Grace Lee</h5>
    <p>Vice President</p>
  </div>
</div>
"""

HTML_STRONG_AND_ANCHOR = """
<ul>
  <li>
    <strong>Henry Taylor</strong>
    <p>Managing Director</p>
  </li>
  <li>
    <strong>Irene Martinez</strong>
    <p>Chief Financial Officer</p>
  </li>
</ul>
"""

HTML_NESTED_ROLE = """
<div>
  <article>
    <h3>Kevin Anderson</h3>
    <div class="info">
      <span class="location">New York</span>
      <div class="title-wrap">
        <span>General Partner</span>
      </div>
    </div>
  </article>
  <article>
    <h3>Laura Thomas</h3>
    <div class="info">
      <span class="location">San Francisco</span>
      <div class="title-wrap">
        <span>Venture Partner</span>
      </div>
    </div>
  </article>
</div>
"""

HTML_H6_HEADING = """
<div>
  <div class="person-card">
    <h6>Monica Chen</h6>
    <p>Board Observer</p>
  </div>
  <div class="person-card">
    <h6>Nathan Park</h6>
    <p>Mentor</p>
  </div>
</div>
"""

HTML_NO_ROLE_FALLBACK = """
<div>
  <div class="staff-bio">
    <h4>Oscar Rivera</h4>
    <p>Joined 2022</p>
  </div>
  <div class="staff-bio">
    <h4>Patricia Kim</h4>
    <p>Joined 2021</p>
  </div>
</div>
"""

HTML_CSS_ID_MATCH = """
<div>
  <div id="team-member-1">
    <h4>Quinn Foster</h4>
    <span>Advisory Board</span>
  </div>
</div>
"""


# ── Layout Tests ───────────────────────────────────


class TestStandardCards:
    def test_extracts_both_names(self):
        soup = BeautifulSoup(HTML_STANDARD_CARDS, "html.parser")
        pairs = extract_name_role_pairs(soup)
        names = {p["name"] for p in pairs}
        assert "Jane Smith" in names
        assert "John Doe" in names

    def test_extracts_roles(self):
        soup = BeautifulSoup(HTML_STANDARD_CARDS, "html.parser")
        pairs = extract_name_role_pairs(soup)
        roles = {p["name"]: p["role"] for p in pairs}
        assert "Managing Partner" in roles["Jane Smith"]
        assert "General Partner" in roles["John Doe"]


class TestCSSClassBased:
    def test_extracts_all_three(self):
        soup = BeautifulSoup(HTML_CSS_CLASS_BASED, "html.parser")
        pairs = extract_name_role_pairs(soup)
        names = {p["name"] for p in pairs}
        assert len(names) >= 3
        assert "Alice Johnson" in names
        assert "Bob Williams" in names
        assert "Carol Davis" in names

    def test_investor_role_matched(self):
        """Investor Relations should match via expanded ROLE_KEYWORDS."""
        soup = BeautifulSoup(HTML_CSS_CLASS_BASED, "html.parser")
        pairs = extract_name_role_pairs(soup)
        carol = [p for p in pairs if p["name"] == "Carol Davis"]
        assert len(carol) >= 1
        assert "Investor" in carol[0]["role"] or "investor" in carol[0]["role"].lower()


class TestGridLayout:
    def test_extracts_all_four(self):
        """Grid layout inside one large container should not be skipped."""
        soup = BeautifulSoup(HTML_GRID_LAYOUT, "html.parser")
        pairs = extract_name_role_pairs(soup)
        names = {p["name"] for p in pairs}
        assert len(names) >= 4
        assert "David Brown" in names
        assert "Grace Lee" in names


class TestStrongTag:
    def test_extracts_from_strong(self):
        """Names in <strong> tags should be found."""
        soup = BeautifulSoup(HTML_STRONG_AND_ANCHOR, "html.parser")
        pairs = extract_name_role_pairs(soup)
        names = {p["name"] for p in pairs}
        assert "Henry Taylor" in names
        assert "Irene Martinez" in names


class TestNestedRole:
    def test_finds_role_deep(self):
        """Role text nested 2+ levels deep should be found."""
        soup = BeautifulSoup(HTML_NESTED_ROLE, "html.parser")
        pairs = extract_name_role_pairs(soup)
        names = {p["name"] for p in pairs}
        assert "Kevin Anderson" in names
        assert "Laura Thomas" in names
        kevin = [p for p in pairs if p["name"] == "Kevin Anderson"]
        assert len(kevin) >= 1
        assert kevin[0]["role"]  # should have found a role


class TestH6Heading:
    def test_extracts_h6_names(self):
        """Names in <h6> headings should be found."""
        soup = BeautifulSoup(HTML_H6_HEADING, "html.parser")
        pairs = extract_name_role_pairs(soup)
        names = {p["name"] for p in pairs}
        assert "Monica Chen" in names
        assert "Nathan Park" in names


class TestNoRoleFallback:
    def test_extracts_names_without_role_keyword(self):
        """Strategy 0 CSS match should still extract names even without strict role keyword."""
        soup = BeautifulSoup(HTML_NO_ROLE_FALLBACK, "html.parser")
        pairs = extract_name_role_pairs(soup)
        names = {p["name"] for p in pairs}
        assert "Oscar Rivera" in names
        assert "Patricia Kim" in names


class TestCSSIdMatch:
    def test_id_attribute_match(self):
        """Elements with team-related id attributes should be found."""
        soup = BeautifulSoup(HTML_CSS_ID_MATCH, "html.parser")
        pairs = extract_name_role_pairs(soup)
        names = {p["name"] for p in pairs}
        assert "Quinn Foster" in names


# ── ROLE_KEYWORDS Tests ────────────────────────────


class TestExpandedRoleKeywords:
    def test_original_keywords_present(self):
        for kw in ["partner", "principal", "associate", "analyst", "founder",
                    "managing", "director", "ceo", "cto", "cfo", "coo"]:
            assert kw in ROLE_KEYWORDS, f"Missing original keyword: {kw}"

    def test_new_keywords_present(self):
        new_kws = [
            "investor", "member", "operator", "observer", "mentor",
            "board", "team", "staff", "manager", "counsel",
            "secretary", "treasurer", "controller", "intern", "resident",
        ]
        for kw in new_kws:
            assert kw in ROLE_KEYWORDS, f"Missing new keyword: {kw}"

    def test_at_least_ten_new(self):
        new_kws = {"investor", "member", "operator", "observer", "mentor",
                    "board", "team", "staff", "manager", "counsel",
                    "secretary", "treasurer", "controller", "intern", "resident"}
        assert len(new_kws & set(ROLE_KEYWORDS)) >= 10
