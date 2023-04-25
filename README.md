# olympus

This is the primary repository for the olympus project.

## INTRODUCTION

The goal of the olympus project is to create a web platform for both
development and deployment. It is designed around regularly-maintained,
enterprise-class software, and it can be scaled up to major deployments and down
to a single, home-based server. The ideal use-case is of a small, local
installation using a number of tiny servers as nodes. The tiny server class
has the advantage of being both cheap to purchase and low on power consumption.
A single, robustly-built data center class server can host olympus, but
power consumption can be the equivalent of 8-10 tiny servers. In its expanded 
configuration, olympus has three core servers:

* Interface (web-facing)
* Supervisor (controller)
* Database/file server

Olympus allows a fourth type of server, the "worker" class, which can be 
spun up or down as needed for processing-intensive tasks. This last type of
node is a good place to use an enterprise-class server, since the occasional
use envisioned of the worker class means that power consumption will
remain reasonable.


## Repositories
## Software stack


## Developer notes for pushing working olympus repository to Github

*Note*: The first series of operations are one-time only, but they may be
repeated as needed should a system require restoration.

### Create bare repository on Github

* Navigate to the [Create a new repository page](https://github.com/new) after
account log-in.
* Under **Repository name**, enter "olympus".
* Under **Description**, enter "Primary repository for the Olympus project."
* Choose the "Public" visibility option.
* Do not add the README file, and leave **Add .gitignore** and **Choose a license**
as *None*. This will create a bare repository, which will facilitate pushing the
existing local repository to github. These files are necessary, though, so be
sure to create them in the local working repository.
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

The passphrase will be regularly needed to add the newly-generated private SSH
key to ssh-agent.

### Add the newly-created public key to Github account settings

* Copy the contents of */home/alex/.ssh/id_github.pub* to the clipboard.
* While logged-in to the Github account, use the account menu drop-down on the
top right to navigate to the [SSH and GPG keys page](https://github.com/settings/keys)
under *Settings*.
* Use the **New SSH key** button to bring up the **SSH keys / Add new** option.
Fill in the options as follows:

**Title**. *Push key from olympus source.*

**Key type**. *Authentication key*

**Key**. Paste in *id_github.pub* from the clipboard.

* Submit the form with the **Add ssh key** button.

### Add a local repository entry for the remote Github repository

On the development machine, change directory to the local working olympus
repository and set up a new remote to handle push/pull commands to/from the
Github repository.

```
git remote add github https://github.com/AlexandreDdaCosta/olympus.git
```

### Add the following lines to *~/ssh/config* 

```
Host github.com
    IdentityFile ~/.ssh/id_github
```

This ensures that the new SSH keypair is loaded whenever ssh-agent is started.

Alternatively, if ssh-agent is already started (next step), use *ssh-add* to add
the identity file to the agent.

```
ssh-add ~/.ssh/id_github
...
Enter passphrase for key '/home/alex/.ssh/id_github':
...
Identity added: /home/alex/.ssh/id_github (alexandre.dias.dacosta@gmail.com)
```

Note that adding a private key to the agent requires that the user enter the
passphrase used to protect the key. Naturally, this assumes that the user has
correctly created the key with password protection.

*Note*: The remaining operations are followed for every push to Github.

### Start ssh-agent.

If working in a terminal, this can happen once per session.

```
eval "$(ssh-agent -s)"
```

**IMPORTANT!** If starting ssh-agent in this manner, be sure that you start
agent **in the same terminal from which you will subsequently issue the git push command!**
Other, existing shell sessions will not be able to access the newly-started
agent.

After starting ssh-agent, use this command to test whether the SSH push is
correctly configured:

```
ssh -T git@github.com
...
Enter passphrase for key '/home/alex/.ssh/id_github':
...
Hi AlexandreDdaCosta! You've successfully authenticated, but GitHub does not
provide shell access.
```

Note that the request for a passphrase will only appear at this stage if the
passphrase hasn't already been entered during the session via *ssh-add*.

Alternatively, ssh-agent can be configured to start automatically on log-in.
For some discussion on this topic,
[read this thread on stackoverflow](https://stackoverflow.com/questions/18880024/start-ssh-agent-on-login).

### Push repository updates to Github

```
git push github
```

Now you can navigate to [the Github repository's home page](https://github.com/AlexandreDdaCosta/olympus).
The header will show an updated commit count as well as updated details for the
latest commit. On [the main home page for the Github account](https://github.com/AlexandreDdaCosta),
the **Contribution activity** section will list the added commits, and the
contribution graph will show an increase in the number of contributions for
that date. 
