# env_file module

## 1. [About](#about) 
## 2. [Supported systems](#supsys)
## 3. [General](#general)
## 4. [Options](#options)
## 5. [Examples](#examples)

<br>
<br>
<br>


## About <a name="about"></a>
Module to set or delete environment files permanently.\
Makes use of the */etc/environment* file

<br>
<br>

## Supported systems <a name="supsys"></a>
Currently supports following operating systems:
* Debian
* Ubuntu
* CentOS
* RedHat

<br>
<br>

## General <a name="general"></a>
**module:** env_file \
**author:** @DKribl \
**version_added:** 2.3 \
**short_description:** Manage environment file

<br>
<br>

## Options <a name="options"></a>

parameter | required | default | choices | comments
--------- | -------- | ------- | ------- | --------
key <br> *(aliases: name)* | yes | None | | environment variable key e.g. <br> * JAVA_HOME <br> * http_proxy ...
value | when state = present | None | | value for defined key
state | yes | present | present <br> absent <br> reloaded | present: adds the environment variable <br> absent: deletes the environment variable <br> reloaded: sources the env file
reload | no | no | yes <br> no | source the environment file
force | no | yes | yes <br> no | overwrite existing variable with new content
<br>
<br>

## Examples <a name="examples"></a>
```
- env_file:
    name: http_proxy
    value: 127.0.0.1
    state: present
    reload: yes

- env_file:
    key: ftp_proxy
    state: absent
    reload: true

- env_file:
    state: reloaded
```
<br>
<br>

[![Powered by Immowelt](https://img.shields.io/badge/powered%20by-immowelt-yellow.svg?colorB=ffb200)](https://stackshare.io/immowelt-group/)