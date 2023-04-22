# olympus

This is the primary repository for the olympus project.

## Developer notes for pushing working olympus repository to Github

*Note*: The first series of operations are one-time only, but may be repeated as needed should a system
need to be restored.

### Create bare repository on Github

* Navigate to the [Create a new repository](https://github.com/new) page after account log-in.
* Under **Repository name**, enter "olympus".
* Under **Description**, enter "Primary repository for the Olympus project."
* Choose the "Public" visibility option.
* Do not add the README file, and leave **Add .gitignore** and **Choose a license** as "None". This will
create a bare repository, which will facilitate pushing the existing local repository to github.
* Press the **Create repository** button.

### Change default branch on Github to "master"

* Navigate to the repository's [gebneral settings page](https://github.com/AlexandreDdaCosta/olympus/settings).
* Edit the **Default branch** to *master* in the edit pop-up and submit.

### Create ssh keypair



```
ssh-keygen -t rsa -b 4096 -C "alexandre.dias.dacosta@gmail.com"

```

*Note*: The remaining operations are followed for every push to Github.

