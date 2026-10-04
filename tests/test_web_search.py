import unittest

from jobpilot.tools.web_search import extract_visible_text


class WebSearchTests(unittest.TestCase):
    def test_extract_visible_text_removes_script_and_navigation_noise(self):
        html = """
        <html>
          <head>
            <title>Senior AI Engineer</title>
            <script>window.secret = "ignore me"</script>
          </head>
          <body>
            <nav>Sign in</nav>
            <main>
              <h1>Senior AI Engineer</h1>
              <p>Build production RAG applications with Python.</p>
              <p>Requirements: LangChain, vector databases, and LLM evaluation.</p>
            </main>
          </body>
        </html>
        """

        text = extract_visible_text(html)

        self.assertIn("Senior AI Engineer", text)
        self.assertIn("Build production RAG applications with Python.", text)
        self.assertNotIn("window.secret", text)
        self.assertNotIn("Sign in", text)


if __name__ == "__main__":
    unittest.main()
