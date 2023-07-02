import libyang
import re
import os
import logging

model_path = 'yang/vendor/cisco/xe/1761'
model_name = 'Cisco-IOS-XE-native'


def validate_models(ctx: libyang.Context, models: list[str]) -> int:
    failed_models = 0
    for model in models:
        if validate_model(ctx, model):
            print(f"[VALIDATED OK]........ {model}")
        else:
            print(f"[VALIDATED FAILED].... {model}")
            failed_models += 1
    return failed_models


def validate_model(ctx: libyang.Context, model_name: str) -> bool:
    libyang.configure_logging(True, logging.ERROR)
    file_path = os.path.join(model_path, model_name)
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            try:
                ctx.parse_module_file(file)
            except libyang.LibyangError:
                return False
    return True


def find_all_argument_xpaths_in_models(folder_path, regex_pattern) -> dict[str, list[str]]:
    file_matches = {}
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and file_name.endswith('.yang'):
            with open(file_path, 'r') as file:
                contents = file.read()
                matches = re.findall(regex_pattern, contents)
                if len(matches) > 0:
                    file_matches[file_name] = matches
    return file_matches


def find_dead_ends_containers(node: libyang.SNode, parent_path="", dead_ends: list[str] = None) -> list[str]:
    if dead_ends is None:
        dead_ends = []
    current_path = f"{parent_path}/{node.module().prefix()}:{node.name()}"  # Construct the current path

    # If the node has the children method, process it.
    if hasattr(node, "children"):
        # If the node has no children, it is a container without any children
        # this means that it is a dead end
        # it could also be a container with presence true, but we don't care about that
        # as some containers with presence true but still have models that augment them
        if sum(1 for _ in node.children()) == 0:
            dead_ends.append(current_path)
        # Recursively traverse child nodes for containers
        for child in node.children():
            find_dead_ends_containers(child, current_path, dead_ends)


if __name__ == '__main__':

    print(f"Finding all argument xpaths in models in folder {model_path}")
    argumenting_models = find_all_argument_xpaths_in_models(model_path, r'(?<=augment \")[\/\w\d\-:]+(?=\" \{)')

    print(f"Loading model {model_name}")
    ctx = libyang.Context(model_path)
    # validate_model(ctx, model_name)

    module: libyang.Module = ctx.load_module(model_name)

    dead_ends_containers: list[str] = []
    node: libyang.SNode
    print(f"Finding dead ends containers in {model_name}")
    for node in module.children():
        find_dead_ends_containers(node, dead_ends=dead_ends_containers)
    resolved_count = 0
    dead_ends_count = len(dead_ends_containers)
    argumenting_model_files_to_be_added = []
    while dead_ends_containers:
        container = dead_ends_containers.pop()
        for key, value in argumenting_models.items():
            if container in value:
                print(f"[OK]........ {container} is in {key} model")
                if key not in argumenting_model_files_to_be_added:
                    argumenting_model_files_to_be_added.append(key)
                resolved_count += 1
                break
        else:
            print(f"[WARNING]... {container} is not in any argumenting models")

    print("\n\n")
    print("*" * 80)
    print(f"Argumenting models to be added for: {model_name}")
    print("\n".join(argumenting_model_files_to_be_added))
    print("\n\n")
    print("*" * 80)
    print(f"Validating models that was found to be argumenting for: {model_name}")
    upstread_models_failed_validation = validate_models(ctx, argumenting_model_files_to_be_added)
    print("*" * 80)
    print(f"number of deadend containers was: {dead_ends_count}")
    print(f"number of resolved dead ends containers was: {resolved_count} in {len(argumenting_model_files_to_be_added)} argumenting models")
    print(f"number of unresolved dead ends containers was: {dead_ends_count - resolved_count}")
    print(f"number of argumenting models that failed validation: {upstread_models_failed_validation}")
    percentage = resolved_count / dead_ends_count * 100
    print(f"percentage of resolved dead ends containers was: {resolved_count / dead_ends_count * 100:.2f}%")
    print(f"percentage of argumenting models that failed validation: {upstread_models_failed_validation / len(argumenting_model_files_to_be_added) * 100:.2f}%")
