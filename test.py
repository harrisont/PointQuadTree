def run_doctests(module, module_dependencies=None):
    """
    @param module_dependencies iteratable(module-with-run_tests-method)
    @return (failure_count, test_count)
    """
    import doctest

    # Test self
    test_results = doctest.testmod(module)

    # Test other modules
    if module_dependencies:
        for module in module_dependencies:
            test_results = tuple(x + y for x,y in zip(test_results, module.run_tests()))

    return test_results
