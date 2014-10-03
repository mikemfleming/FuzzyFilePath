"""
	get word at cursor
"""
from FuzzyFilePath.FuzzyFilePath import get_word_at_cursor


def should_return_word_at_cursor(test):
	test.set_line('notPartOfPath	/absolute/pathAtCursor	')
	test.move_cursor(0, 25)

	word = get_word_at_cursor(test.view)
	assert True == False
	print(word)


def should_return_empty_string(test):
	word = get_word_at_cursor(test.view)
	print("emptystring:", word)


# export
tests = [
	should_return_word_at_cursor,
	should_return_empty_string,
]