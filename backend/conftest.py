# Marks backend/ as the pytest rootdir so tests can `import engine`.
# pytest's default (prepend) import mode adds this directory to sys.path,
# which makes the `engine` package importable without an installed wheel.
