import os


def file_search(curr_path, searching_file):
    if isinstance(curr_path, str):
        files = os.listdir(curr_path)
        path = curr_path + ("" if curr_path[-1] == "\\" else "\\")
        if searching_file in files:
            return path + searching_file
        folders = []
        for file in files:
            if os.path.isdir(path + file):
                folders.append(path + file)
        return file_search(folders, searching_file)
    elif isinstance(curr_path, list):
        if not curr_path:
            return None
        folders = []
        for folder in curr_path:
            try:
                path = folder + ("" if curr_path[-1] == "\\" else "\\")
                listdir = os.listdir(folder)
                if searching_file in listdir:
                    return path + searching_file
                else:
                    folders += [path + file for file in listdir if os.path.isdir(path + file)]
            except Exception as e:
                print("К папке", folder, "няма доступу")
        return file_search(folders, searching_file)


def files_search(curr_path, searching_file):
    if isinstance(curr_path, str):
        files = os.listdir(curr_path)
        path = curr_path + ("" if curr_path[-1] == "\\" else "\\")
        folders = []
        for file in files:
            if searching_file in file:
                yield path + file
            if os.path.isdir(path + file):
                folders.append(path + file)
        if folders:
            for file in files_search(folders, searching_file):
                yield file
    elif isinstance(curr_path, list):
        if not curr_path:
            return None
        folders = []
        for folder in curr_path:
            try:
                path = folder + ("" if curr_path[-1] == "\\" else "\\")
                listdir = os.listdir(folder)
                for file in listdir:
                    if searching_file in file:
                        yield path + file
                else:
                    folders += [path + file for file in listdir if os.path.isdir(path + file)]
            except Exception as e:
                print("На папке", folder, "ошибка:", e)
        for file in files_search(folders, searching_file):
            yield file


if __name__ == "__main__":
    files = [file for file in files_search("B:\\", ".iso")]
    files.sort()
    for file in files:
        print(file)
