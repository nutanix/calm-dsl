def get_states_filter(STATES_CLASS, state_key="state"):

    states = []
    for field in vars(STATES_CLASS):
        if not field.startswith("__"):
            states.append(getattr(STATES_CLASS, field))
    state_prefix = ",{}==".format(state_key)
    return ";({}=={})".format(state_key, state_prefix.join(states))
