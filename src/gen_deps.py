import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Generator, Set, Union

# use this script with the command `python  src/gen_deps.py C:/Users/amy36/PycharmProjects/doppelganger  src > dependencies.json`
class GenerateDependency:
    def __init__(
            self, root_path: str, package_name: str, group_packages: Set[str] = set()
    ) -> None:
        self._root_path = Path(root_path)
        self._package_name = package_name
        self._group_packages = group_packages
        self._internal_packages = None

    @classmethod
    def iter_py_files(
            cls, directory_path: Union[Path, str], extension="py"
    ) -> Generator[Path, None, None]:
        """Get all the files under a directory with specific extension"""
        yield from Path(directory_path).rglob(f"*.{extension}")

    def get_internal_packages(self) -> Set[str]:
        """Get all the internal packages for a project"""
        if self._internal_packages is None:
            python_path = self._root_path.resolve()
            # Return package names as strings instead of Paths
            self._internal_packages = {
                self.filename_to_module(directory, self._root_path)
                for directory in python_path.iterdir()
                if directory.is_dir() and (directory / "__init__.py").exists()
            }
        return self._internal_packages

    def _is_internal_package(self, module_name: str) -> bool:
        """Check if a module is part of the internal project packages"""
        return any(module_name.startswith(internal_pkg) for internal_pkg in self.get_internal_packages())

    def filename_to_module(
            cls, filepath: Union[Path, str], root_path: Union[Path, str]
    ) -> str:
        """Given a filepath and a root_path derive the module name as in import statement"""
        realpath = str(Path(filepath).relative_to(root_path))
        realpath = realpath.replace("\\", ".")
        realpath = realpath.replace("/", ".")
        realpath = realpath.split(".py")[0]
        if realpath.endswith(".__init__"):
            realpath = realpath.split(".__init__")[0]
        return realpath

    def _get_all_imports_of_file(self, filename: Path) -> Set[str]:
        """Get all imports of a file, filtering for internal packages"""
        current_module = self.filename_to_module(filename, self._root_path)
        if filename.name == "__init__.py":
            current_module += ".__init__"

        imports = set()
        for node in ast.walk(
                ast.parse(source=filename.read_text(encoding="utf8"), filename=filename)
        ):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if self._is_internal_package(name.name):
                        imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                # Reconstruct the full module path
                added = set()
                if node.level == 0:
                    module = node.module
                else:
                    module = ".".join(current_module.split(".")[: -node.level])
                    if node.module:
                        module += "." + node.module

                for name in node.names:
                    full_module = module + "." + name.name if module else name.name

                    # Check if the full module is an internal package
                    if self._is_internal_package(full_module):
                        added.add(full_module)
                    elif module and self._is_internal_package(module):
                        added.add(module)

                imports.update(added)

        return imports

    def get_import_map(self) -> DefaultDict[str, Set[str]]:
        """Get import mapping for internal modules only"""
        imports = defaultdict(set)
        internal_packages = self.get_internal_packages()

        for file in self.iter_py_files(self._root_path / self._package_name):
            file_imports = self._get_all_imports_of_file(file)
            current_module = self.filename_to_module(file, self._root_path)

            # Only process if the current module is internal
            if self._is_internal_package(current_module):
                imports[current_module].update(
                    {_import for _import in file_imports
                     if _import != current_module}  # Exclude self-imports
                )

        return imports

    def make_json_file(self) -> str:
        """Convert import map to JSON"""
        import_map = self.get_import_map()
        # Convert set to list for JSON serialization
        json_map = {k: list(v) for k, v in import_map.items() if v}
        return json.dumps(json_map, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-g", "--group", help="group module name", type=argparse.FileType("r")
    )
    parser.add_argument("project_path")
    parser.add_argument("package_name")

    args = parser.parse_args()
    if args.group:
        groups = {line.strip() for line in args.group.readlines() if line.strip()}
        generate_dependency = GenerateDependency(
            args.project_path, args.package_name, groups
        )
    else:
        generate_dependency = GenerateDependency(args.project_path, args.package_name)
    print(generate_dependency.make_json_file())


if __name__ == "__main__":
    main()