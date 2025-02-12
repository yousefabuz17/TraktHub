SRC_FILES := $(wildcard src/trakt_hub/*.py)
TEST_FILES := $(wildcard tests/*.py)
FUNC_FILES := $(wildcard src/trakt_hub/trakt_functions/*.py)
UTIL_FILES := $(wildcard src/trakt_hub/trakt_utils/*.py)


format:
	black $(SRC_FILES) $(TEST_FILES) $(FUNC_FILES) $(UTIL_FILES)

black: format