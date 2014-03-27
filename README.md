# jbinto/ansible-play

Following tutorial to create idempotent, repeatable provisioning script for Rails applications (among other things) using Ansible.

http://ihassin.wordpress.com/2013/12/15/from-zero-to-deployment-vagrant-ansible-rvm-and-capistrano-to-deploy-your-rails-apps-to-digitalocean-automatically/

Adapted as necessary.

## Issues

* Can't include RSA keys in the git repo. Run `ssh-keygen` and create a deploy keypair, and move it to `devops/templates/deploy_rsa[.pub]`.

* Not sure if the deploy keypair should have a passphrase on it or not? Well, I am sure, *it should*, but whether automation relies on this or not?

## Usage

Install Vagrant:
http://www.vagrantup.com/downloads.html

I'm using 1.5.1 for OS X.

#
```
brew install ansible
vagrant up web
```

## OS X March 2014 note

If you get the following error installing ansible:

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
