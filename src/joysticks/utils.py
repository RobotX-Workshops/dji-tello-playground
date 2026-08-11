def print_state(state_dict: dict, indent: str = "") -> None:
    for k, v in state_dict.items():
        if isinstance(v, dict):
            print(f"{indent}{k}:")
            print_state(v, indent + "  ")
        else:
            print(f"{indent}{k}: {v}")
