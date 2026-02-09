from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression, Qt

class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("darkBlue"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = [
            "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE",
            "CREATE", "TABLE", "DROP", "ALTER", "INDEX", "Go", "USE", "IF", "EXISTS",
            "Left", "Right", "Outer", "Inner", "Join", "On", "Group", "By", "Order", "Limit",
            "AND", "OR", "NOT", "NULL", "AS", "IN", "IS", "LIKE", "DISTINCT", "COUNT",
            "MAX", "MIN", "SUM", "AVG", "PRIMARY", "KEY", "AUTO_INCREMENT", "DEFAULT"
        ]

        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b", QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.highlighting_rules.append((pattern, keyword_format))
            
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("gray"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression("--[^\n]*"), comment_format))
        self.highlighting_rules.append((QRegularExpression("#[^\n]*"), comment_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("darkGreen"))
        self.highlighting_rules.append((QRegularExpression("\".*\""), string_format))
        self.highlighting_rules.append((QRegularExpression("'.*'"), string_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
