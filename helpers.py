def setup(page, port):
    # Set VEGA_URL using window._env_. Double curly braces are used to escape so the js is valid
    window_env = f"window._env_ = Object.assign({{}}, window._env_, {{ VEGA_URL: 'http://localhost:{port}/graphql' }})"
    page.add_init_script(
        script=window_env
    )