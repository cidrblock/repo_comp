
import importlib.resources



def main() -> None:
    """Load the configuration data file"""

    data_dir = importlib.resources.files("repo_comp").joinpath("data")
    data_file = data_dir.joinpath("repo.toml")
    contents = data_file.read_text()

    print(contents)




if __name__ == '__main__':
    main()