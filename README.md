# jbinto/ansible-ubuntu-rails-server

## tl;dr

[Ansible](http://docs.ansible.com/index.html) playbook to provision a Rails deployment server with:

* Ubuntu 12.04
* Postgresql 9.3
* rbenv
* ruby 2.1.1
* Phusion Passenger + nginx from official apt repo

## Overview

Following various sources to create an idempotent, repeatable provisioning script for Rails applications (among other things) using Ansible.

My current goal is to be able to deploy a Rails / Postgres / PostGIS app to DigitalOcean in "one click". Perhaps "many clicks", but as minimal human intervention as possible.

Repeatably. Possibly even including provisioning of the cloud instances.

At the very least, to create a consistent set of DEV, STAGING and PROD environments.

Benefits to using something like Ansible to manage servers:

* Reduce "[jenga](https://www.youtube.com/watch?v=I7H6wGy5zf4)" feeling when running servers (same win as unit testing and source control)
* Consistency between different environments
* Executable documentation
* Combined with cloud providers and hourly billing, can create on-demand staging environments

## Usage

[Vagrant](http://www.vagrantup.com/downloads.html) must be installed from the website.

Install Ansible and clone the repo.

```
brew install ansible

git clone https://github.com/jbinto/ansible-ubuntu-rails-server.git
cd ansible-ubuntu-rails-server
```

Generate a crypted password, and put it in `vars/default.yml`.

```
python support/generate-crypted-password.py
```

The following command will:

* Use Vagrant to create a new Ubuntu virtual machine.
* Boot that machine with Virtualbox.
* Ask you for the `deploy` sudo password (the one you just crypted).
* Use our Ansible playbook to provision everything needed for the Rails server.

```
vagrant up
```

**BUG:** Sometimes, `vagrant up` times out before Ansible gets a chance to connect. I haven't figured this out yet. If this happens, run `vagrant provision` to continue the Ansible playbook.

To run individual roles (e.g. only install nginx), try the following. You can replace `nginx` with any role name, since they're all tagged in `build-server.yml`.

```
ansible-playbook build-server.yml -i hosts --tags nginx
```

Once the provision is complete, continue to [jbinto/rails4_sample_app_capistrano](https://github.com/jbinto/rails4_sample_app_capistrano) to deploy a Rails application using Capistrano.

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

* ~~Can't include RSA keys in the git repo. Run `ssh-keygen` and create a deploy keypair, and move it to `devops/templates/deploy_rsa[.pub]`.~~ (Not using deploy keys, but ssh-agent forwarding instead.)

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


## Issues with Passenger - solved

There's two ways to install Passenger:

* Using their official Ubuntu packages, which installs Passenger files in various locations throughout the system (n.b. as do all apt packages)
* Your `passenger_root` must be a `locations.ini` file which points to all these locations. This ships with the passenger package and can also be generated with one of the `passenger-config about` commands.

Or...

* `gem install passenger` (or adding `passenger` to `Gemfile`), which contains all Passenger files in your rubygems directory.
* `install-passenger-nginx-module`, which compiles a brand new nginx and installs it into `/opt/nginx`. [Nginx modules must be statically loaded.](https://github.com/phusion/passenger/wiki/Why-can't-Phusion-Passenger-extend-my-existing-Nginx%3F).

The former makes more sense, since it's apt it seems cleaner/more maintainable. Especially for nginx, I don't want to have to be recompiling if I need a new module or security update.

I spent a long time trying to figure out why nginx returned `403 Forbidden` for anything not in `./public`.

I was defining `passenger_ruby` in my server-specific config, but forgetting `passenger_root`. I ended up putting these two lines in `/etc/nginx/nginx.conf`, and now all is well. In my server specific config, I only have `passenger_enabled`.

## Things that still need fixing

* Security: 5minbootstrap
* Security: Get rid of vagrant user
* Security: Analyze exactly why we need NOPASSWD. Capistrano symlink stuff maybe can be done in Ansible, and if cap needs sudo, could restrict it to particular commands.
* Restart nginx automagically after deploys? Still have to ssh in and do it manually. Not sure why.
* Asset precompilation using official capistrano method - this happens on remote server?
* Deploy user still might still be hardcoded some places - try renaming it
* Provision to DigitalOcean!
* `ag BUG; ag NOTE`

## Sources / references

Synthesized from the following sources:

* [From Zero to Deployment: Vagrant, Ansible, Capistrano 3 to deploy your Rails Apps to DigitalOcean automatically (part 1)](http://ihassin.wordpress.com/2013/12/15/from-zero-to-deployment-vagrant-ansible-rvm-and-capistrano-to-deploy-your-rails-apps-to-digitalocean-automatically/)
* [leucos/ansible-tuto](https://github.com/leucos/ansible-tuto)
* [leucos/ansible-rbenv-playbook](https://github.com/leucos/ansible-rbenv-playbook)
* [dodecaphonic/ansible-rails-app](https://github.com/dodecaphonic/ansible-rails-app/)
* [Ansible: List of All Modules](http://docs.ansible.com/list_of_all_modules.html) (easiest way to find module docs, CMD+F / CTRL+F)
* [Phusion Passenger users guide, Nginx edition](http://www.modrails.com/documentation/Users%20guide%20Nginx.html)
