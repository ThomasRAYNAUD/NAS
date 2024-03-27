import os

GNS3_Project_Name = "Conf_Finale"
dynamips_directory = "/home/hipp/GNS3/projects/Documents/project-files/dynamips"


if __name__ == "__main__":
    print("Suppression de tous les fichiers config des routers\n Assurez-vous que le projet GNS3 est bien fermé")

    for subdir in os.listdir(dynamips_directory):
        subdir_path = os.path.join(dynamips_directory, subdir)
        if os.path.isdir(subdir_path):
            configs_path = os.path.join(subdir_path, "configs")
            if os.path.isdir(configs_path):
                for file in os.listdir(configs_path):
                    if file.endswith("startup-config.cfg"):
                        file_path = os.path.join(configs_path, file)
                        os.remove(file_path)
                        print(f"Supprimé : {file}")
 