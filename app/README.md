# jbinto/ansible-play

Following tutorial to create idempotent, repeatable provisioning script for Rails applications (among other things) using Ansible.

http://ihassin.wordpress.com/2013/12/15/from-zero-to-deployment-vagrant-ansible-rvm-and-capistrano-to-deploy-your-rails-apps-to-digitalocean-automatically/

Adapted as necessary.

## Issues

* Can't include RSA keys in the git repo. Run `ssh-keygen` and create a deploy keypair.

* Not sure if the deploy keypair should have a passphrase on it or not? Well, I am sure, *it should*, but whether automation relies on this or not?


