# olympus

This is the primary repository for the olympus project.

## Developer notes for pushing working olympus repository to Github

*Note*: The first series of operations are one-time only, but may be repeated as needed should a system
need to be restored.

### Create bare repository on Github

* Navigate to the [Create a new repository page](https://github.com/new) after account log-in.
* Under **Repository name**, enter "olympus".
* Under **Description**, enter "Primary repository for the Olympus project."
* Choose the "Public" visibility option.
* Do not add the README file, and leave **Add .gitignore** and **Choose a license** as *None*. This will
create a bare repository, which will facilitate pushing the existing local repository to github.
* Submit with the **Create repository** button.

### Change default branch on Github to "master"

* Navigate to [the repository's general settings page](https://github.com/AlexandreDdaCosta/olympus/settings).
* Edit the **Default branch** to *master* in the edit pop-up and submit.

### Create ssh keypair under account on local development machine

The command for this is "ssh-keygen" and proceeds as follows:

```
ssh-keygen -t rsa -b 4096 -C "alexandre.dias.dacosta@gmail.com"
Generating public/private rsa key pair.
Enter file in which to save the key (/home/alex/.ssh/id_rsa): /home/alex/.ssh/id_github
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
```

The passphrase will be needed to add the newly-generated private SSH key to ssh-agent.

###  Add the newly-created public key to Github account settings.

* Copy the contents of */home/alex/.ssh/id_github.pub* to the clipboard.
* Navigate to [the repository's general settings page](https://github.com/AlexandreDdaCosta/olympus/settings).
* While logged-in to the Github account, use the account menu drop-down to navigate to the [SSH and GPG keys page](https://github.com/settings/keys)
under *Settings*.
* Use the **New SSH key** button to bring up the **SSH keys / Add new** option. Fill in the options as follows:

**Title** *Push key from olympus source.*
**Key type** *Authentication key*
**Key** Paste in *id_github.pub* from the clipboard.

* Submit the form with the **Add ssh key** button.

*Note*: The remaining operations are followed for every push to Github.

