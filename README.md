# jbinto/ansible-play

Following tutorial to create idempotent, repeatable provisioning script for Rails applications (among other things) using Ansible.

http://ihassin.wordpress.com/2013/12/15/from-zero-to-deployment-vagrant-ansible-rvm-and-capistrano-to-deploy-your-rails-apps-to-digitalocean-automatically/

Adapted as necessary.

## Usage

Install Vagrant:
http://www.vagrantup.com/downloads.html

I'm using 1.5.1 for OS X.

#
```
brew install ansible

git clone https://github.com/jbinto/ansible-play.git
cd ansible-play/app
vagrant up

ansible-playbook devops/webserver.yml -i devops/webhosts -vvvv
ansible-playbook devops/postgres.yml -i devops/webhosts -vvvv
ansible-playbook devops/rbenv.yml -i devops/webhosts -vvvv -K
```

## Notes

* Vagrant ships with insecure defaults. Can log in to the VM with `vagrant/vagrant`, and there is an insecure SSH key. Need to destroy this stuff.

* `vagrant` is a NOPASSWD sudoer, but `deploy` requires a password. Should I just run all the scripts with `-K?

* It seems so. From googling, it seems Ansible [is not designed to be run with the sudoers file only allowing pre-approved commands.](https://serverfault.com/questions/560106/how-can-i-implement-ansible-with-per-host-passwords-securely)

* It seems just having a `deploy` user is a bad idea. It's messy. Perhaps there should be a `provision` user as well. This user could install packages, etc. and `deploy` should only affect have rights to the app in `~/deploy`.

* For now, keep it simple, just `deploy`. But we won't go down the `NOPASSWD` route. It's too risky. Consider: if there's any bug in Rails that allowed remote code execution, attackers are one `sudo` away from full control.

* The pros of disabling `NOPASSWD` outweigh the cons. Should make it standard practice when creating an Ansible playbook: create a `deploy` user with a unique password, use that password for sudo, and always pass `-K` when necessary. Design playbooks to be clear about whether it requires sudo or not. Right now it's very muddy with privileged and unprivileged tasks combined in the same play.

* In order to "destroy Vagrant", basically we just remove the `vagrant` user. Also, lock down SSH, etc (see `phred/5minbootstrap`.)

* This means only one playbook should be executed as `vagrant`: the one that sets up the `deploy` user. Every script afterwards *must* be executable as `deploy`.

* ~~Despite that, I still can't get `ansible-playbook` to work with the `vagrant` user, because my SSH key isn't moved there.~~ **UPDATE**: This was because I was overwriting `/etc/sudoers`. This gave `deploy` sudo access, but made everyone else (including `vagrant`) lose it.

* Can't include RSA keys in the git repo. Run `ssh-keygen` and create a deploy keypair, and move it to `devops/templates/deploy_rsa[.pub]`.

* Not sure if the deploy keypair should have a passphrase on it or not? Well, I am sure, *it should*, but whether automation relies on this or not?

* If you get the following error installing ansible on OS X Mavericks:

```
# clang: error: unknown argument: '-mno-fused-madd' [-Wunused-command-line-argument-hard-error-in-future]
```

Run: 

```
echo "ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future" >> ~/.zshrc
. ~/.zshrc
brew install ansible
```

See [Stack Overflow question](https://stackoverflow.com/questions/22390655/ansible-installation-clang-error-unknown-argument-mno-fused-madd) for details.
