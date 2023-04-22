# olympus

This is the primary repository for the olympus project.

## Developer notes for pushing working olympus repository to Github

*Note*: The first series of operations are one-time only, but they may be repeated as needed should a system
require restoration.

### Create bare repository on Github

* Navigate to the [Create a new repository page](https://github.com/new) after account log-in.
* Under **Repository name**, enter "olympus".
* Under **Description**, enter "Primary repository for the Olympus project."
* Choose the "Public" visibility option.
* Do not add the README file, and leave **Add .gitignore** and **Choose a license** as *None*. This will
create a bare repository, which will facilitate pushing the existing local repository to github. These
files are necessary, though, so be sure to create them in the local working repository.
* Submit with the **Create repository** button.

### Change default branch on Github to "master"

* Navigate to [the repository's general settings page](https://github.com/AlexandreDdaCosta/olympus/settings).
* Edit the **Default branch** to *master* in the edit pop-up and submit.

### Create ssh keypair under account on local development machine

The command for this is "ssh-keygen" and proceeds as follows:

```
ssh-keygen -t rsa -b 4096 -C "alexandre.dias.dacosta@gmail.com"
...
Generating public/private rsa key pair.
...
Enter file in which to save the key (/home/alex/.ssh/id_rsa): /home/alex/.ssh/id_github
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
```

The passphrase will be regularly needed to add the newly-generated private SSH key to ssh-agent.

###  Add the newly-created public key to Github account settings.

* Copy the contents of */home/alex/.ssh/id_github.pub* to the clipboard.
* While logged-in to the Github account, use the account menu drop-down on the top right to navigate to the 
[SSH and GPG keys page](https://github.com/settings/keys) under *Settings*.
* Use the **New SSH key** button to bring up the **SSH keys / Add new** option. Fill in the options as follows:

**Title**. *Push key from olympus source.*

**Key type**. *Authentication key*

**Key**. Paste in *id_github.pub* from the clipboard.

* Submit the form with the **Add ssh key** button.

### On the development machine, change directory to the local working olympus repository and set up a new remote to handle push/pull commands to/from the Github repository.

```
git remote add github https://github.com/AlexandreDdaCosta/olympus.git
```

### Add the following lines to *~/ssh/config* 

```
Host github.com
    IdentityFile ~/.ssh/id_github
```

This ensures that the new SSH keypair is loaded whenever ssh-agent is started.

*Note*: The remaining operations are followed for every push to Github.

### Start ssh-agent.

If working in a terminal, this can happen once per session.

```
eval "$(ssh-agent -s)"
```

**IMPORTANT!** If starting ssh-agent in this manner, be sure that you start agent **in the same terminal from which you will
subsequently issue the git push command!**

After starting ssh-agent, use this command to test whether the SSH push is correctly configured:

```
ssh -T git@github.com
...
Enter passphrase for key '/home/alex/.ssh/id_github':
...
Hi AlexandreDdaCosta! You've successfully authenticated, but GitHub does not provide shell access.
```

Alternatively, ssh-agent can be configured to start automatically on log-in. For some discussion on this topic,
[read this thread on stackoverflow](https://stackoverflow.com/questions/18880024/start-ssh-agent-on-login). The best
option is a systemd user service.

### Once all code for the push has been committed to the local repository, push all updates to Github.  

```
git push github
```

Now you can navigate to [the Github repository's home page](https://github.com/AlexandreDdaCosta/olympus). The header
will show an updated commit count as well as updated details for the latest commit. On
[the main home page for the Github account](https://github.com/AlexandreDdaCosta),
the **Contribution activity** section will list the added commits, and the
contribution graph will show an increase in the number of contributions for that date. 
