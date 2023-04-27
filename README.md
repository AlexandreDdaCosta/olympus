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

TODO

## Software stack

TODO

## Developer notes for pushing working olympus repository to Github

### Set up ssh key pair

A user account on olympus is allowed ssh access via an ssh key pair. The public
key is stored in salt pillar and pushed to minions by Saltstack.

The key pair should be created using the Ed25519 algorithm on the user's home
(or *originating*) server. Here's an example of such a procedure on a Mac,
following the defaults:

```
ssh-keygen -t ed25519 -C "alexandre.dias.dacosta@gmail.com"
...
Generating public/private ed25519 key pair.
Enter file in which to save the key (/Users/alex/.ssh/id_ed25519):
Enter passphrase (empty for no passphrase):
...
Enter same passphrase again:
...
Your identification has been saved in /Users/alex/.ssh/id_ed25519.
Your public key has been saved in /Users/alex/.ssh/id_ed25519.pub.
The key fingerprint is:
SHA256:SqZg///RklSF2X5cLixQo/b7b/udlpAiMGaheZAbUPQ alexandre.dias.dacosta@gmail.com
The key's randomart image is:
+--[ED25519 256]--+
|   .+o.    .o+.  |
|     +..  ..oo. .|
|      *E. o..o o.|
|     + * . o. + +|
|  o   * S . ...o |
| . o + . o + +   |
|    o .   = + . .|
|     .     o . o+|
|      .....   o=*|
+----[SHA256]-----+
```

It's important to protect the private key with a strong passphrase.

In this example, the contents of **id_ed25519.pub** needs to be added to the
user's configuration in salt pillar under the stanza *ssh_public_key*. An
administrator then needs to run the *users* state file on all salt minions to
grant the user system-wide ssh access.

```
sudo -i salt '*' state.sls users -v
```

At this point, the account for this user on every salt minion will have an
*/.ssh* directory off */home* that looks similar to the following:

```
alex@zeus:~$ ls -l ~/.ssh
total 12
-rw-r----- 1 alex alex  114 Apr 26 18:50 authorized_keys
-rw-r----- 1 alex alex   93 Apr 26 18:54 config
```

The *authorized_keys* file will contain the newly-installed public key. The
other file, *config*, is also maintained by salt, meaning that it will be
overwritten on each subsequent run of the *users.sls* state. The contents of
*config* are as follows:

```
Host 192.168.1.*
 ForwardAgent yes
Host github.com
 ForwardAgent yes
Host *
 ForwardAgent no
```

* This configuration enables a feature known as *agent forwarding*, which means
that the same ssh key used to log in to olympus will be automatically
used when continuing a chain of ssh sessions.
* The first two lines ensure that the user's ssh key continues to be used as the
user moves from one olympus server to another.
* Lines three and four ensure that the user's ssh key will be used when 
attempting to push code to a Github repository.
* The last two lines are a safety feature needed due to a vulnerability in
ssh-agent known as *agent hijacking*. In general, it's good practice not to
automatically allow agent forwarding unless you are **VERY SURE** that the
remote server can be trusted.

Notice that, for this procedure to work, the user's **originating** server (not
olympus) **MUST** be running *ssh-agent*. It's common for a modern operating
system to automatically start *ssh-agent* when a user opens a shell window from
a GUI interface. On the first ssh attempt, *ssh-agent* will ask for and save the
passphrase associated with the ssh key pair. This passphrase entry typically
lasts at least as long as the user is logged into the originating server.

This set-up needs to be done only once. But, in order to push code to Github,
there are a few more steps.

### Create a bare repository on Github

* A one-time operation when adding an olympus repository to Github.
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

* Also a one-time operation.
* Navigate to [the repository's general settings page](https://github.com/AlexandreDdaCosta/olympus/settings).
* Edit the **Default branch** to *master* in the edit pop-up and submit.

### Add any desired public keys to Github account settings

* Copy the contents of a public key to the clipboard.
* While logged-in to the Github account, use the account menu drop-down on the
top right to navigate to the [SSH and GPG keys page](https://github.com/settings/keys)
under *Settings*.
* Use the **New SSH key** button to bring up the **SSH keys / Add new** option.
Fill in the options as follows:

**Title**. *Push key from olympus source.*

**Key type**. *Authentication key*

**Key**. Paste in the public key contents from the clipboard.

* Submit the form with the **Add ssh key** button.
* The steps under this header can be repeated when updating an old key or adding 
more keys to the Github account.

### Add a local repository entry for the remote Github repository

Back on the olympus development machine, change directory to the local working
olympus repository and set up a new remote to handle push/pull commands to/from
the Github repository.

```
git remote add github https://github.com/AlexandreDdaCosta/olympus.git
```

At this point, you can use this command to test whether the ssh push is
correctly configured:

```
ssh -T git@github.com
...
Hi AlexandreDdaCosta! You've successfully authenticated, but GitHub does not
provide shell access.
```

All previous steps are one-time only **UNLESS** you want to make modifications to
repositories or ssh key pairs.

### Push repository updates to Github

Once all the set-up is done, you can push reliably code to Github from inside
the remote repository:

```
git push github
```

Now you can navigate to [the Github repository's home page](https://github.com/AlexandreDdaCosta/olympus).
The header will show an updated commit count as well as updated details for the
latest commit. On [the main home page for the Github account](https://github.com/AlexandreDdaCosta),
the **Contribution activity** section will list the added commits, and the
contribution graph will show an increase in the number of contributions for
that date. 
