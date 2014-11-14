# jbinto/ansible-ubuntu-rails-server

## tl;dr

[Ansible](http://docs.ansible.com/index.html) playbook to provision a Rails deployment server with:

* Ubuntu 14.04.1
* Postgresql 9.3
* rbenv
* ruby 2.1.5
* [Phusion Passenger](https://www.phusionpassenger.com/) + nginx from Phusion's apt repo
* [Papertrail logging](https://papertrailapp.com/)
* Prepares an nginx vhost for a Rails app, ready for deployment with `cap`

It can be deployed locally using [Vagrant](http://www.vagrantup.com/) (i.e. for DEV environment), or in the cloud using [Digital Ocean](https://www.digitalocean.com/) (i.e. STAGING/PROD environments).

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

## Usage (Vagrant)

[Vagrant](http://www.vagrantup.com/downloads.html) must be installed from the website.

I'm currently retrieving Ansible from git, as well as the `dopy` module for DigitalOcean.

```
git clone https://github.com/jbinto/ansible-ubuntu-rails-server.git
cd ansible-ubuntu-rails-server
sudo pip install -r requirements.txt
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

## Usage (DigitalOcean)

Set up environemnt variables `DO_CLIENT_ID` and `DO_API_KEY`, or hardcode them in `./hosts/digital_ocean.ini`.

Install `tugboat`:

```
gem install tugboat
tugboat authorize
```

Edit `./vars/digitalocean.yml`. 

* Note that `hostname` must be a real FQDN you own, and the DNS must be pointing to DigitalOcean.
* You can use `tugboat` to acquire the magic numbers needed for region/image/size IDs.

Now you can provision the DigitalOcean droplet:

```
ansible-playbook -i local provision-digitalocean.yml
```

This will spin up a new DigitalOcean VPS **which costs real money**. Since you set up the SSH keys with DigitalOcean, you already have passwordless `root` access.

At the end, it should tell you the new IP address of your server (doesn't seem to be doing this anymore c. 10-2014).

* **Manually** add the IP address to `./hosts-digitalocean`.
* **Manually** set your DNS as necessary with this new IP address. (**TODO use digital_ocean_domain module**)
* Generate a crypted password, if not already done, and put it in `vars/default.yml`. This will be the password for your `deploy` user.

```
python support/generate-crypted-password.py
```

Now, run the playbook as usual. Good luck!

```
ansible-playbook build-server.yml -i hosts-digitalocean -u root -K -vvvv
```

Note that after the first run, `root` will no longer be able to log in. To run the playbook again, replace `root` with the `deploy` user as set in `vars/defaults.yml`.

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

* `ag BUG; ag NOTE`
* Security: 5minbootstrap
* Asset precompilation using official capistrano method - this happens on remote server?
* Create a Vagrant Cloud box with some or all of the Ansible steps already completed.
* The stages are a little muddy. The current example targets only `RAILS_ENV=production`, regardless of whether it's Vagrant (dev) or DigitalOcean (could be staging, could be prod). Can easily edit the role as needed, but need to devise a better overall strategy.

## Fixed issues / answered questions

* ~~Security: Get rid of vagrant user~~ **UPDATE:** This isn't necessary. I'm only ever running `vagrant` on my local machine, and that user is truly necessary for plumbing. We'll never pacakge the Vagrant image and deploy it to the cloud. We can assume a clean base (e.g. DigitalOcean).
* ~~Security: Analyze exactly why we need NOPASSWD. Capistrano symlink stuff maybe can be done in Ansible, and if cap needs sudo, could restrict it to particular commands.~~ **UPDATE:** Fixed this by moving the symlinking, nginx stuff to Ansible, which is better suited for that anyway. Now, cap should be fine without sudo.
* ~~Restart nginx automagically after deploys? Still have to ssh in and do it manually. Not sure why.~~ **UPDATE:** Fixed.
* ~~Deploy user still might still be hardcoded some places - try renaming it~~ **done**
* ~~Provision to DigitalOcean!~~ **done**
* ~~Shouldn't have to SSH in to set postgres password in database.yml.~~ **done**
* ~~Only update the apt cache once every N. (60 minutes? 24 hours? What if we need to force it? -- easy, use a update_apt_cache handler on all things that need it, e.g. added repos)~~ **done**

## Sources / references

Synthesized from the following sources:

* [From Zero to Deployment: Vagrant, Ansible, Capistrano 3 to deploy your Rails Apps to DigitalOcean automatically (part 1)](http://ihassin.wordpress.com/2013/12/15/from-zero-to-deployment-vagrant-ansible-rvm-and-capistrano-to-deploy-your-rails-apps-to-digitalocean-automatically/)
* [leucos/ansible-tuto](https://github.com/leucos/ansible-tuto)
* [leucos/ansible-rbenv-playbook](https://github.com/leucos/ansible-rbenv-playbook)
* [dodecaphonic/ansible-rails-app](https://github.com/dodecaphonic/ansible-rails-app/)
* [Ansible: List of All Modules](http://docs.ansible.com/list_of_all_modules.html) (easiest way to find module docs, CMD+F / CTRL+F)
* [Phusion Passenger users guide, Nginx edition](http://www.modrails.com/documentation/Users%20guide%20Nginx.html)
