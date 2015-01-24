## React / Flux Modules

This is the Source folder for the  React / Flux Modules.  The idea is to decouple the UI from the API and create a [isomorphic JavaScript](http://nerds.airbnb.com/isomorphic-javascript-future-web-apps/) ecosystem.

It is also using [canon-bootstrap](https://github.com/rackerlabs/canon-bootstrap) so we can use both [Canon](http://rackerlabs.github.io/canon/) and [Bootstrap](http://getbootstrap.com/) components together.  There are a number of existing React Bootstrap components, including [React Bootstrap](http://react-bootstrap.github.io/) which should make development faster.

## [React / Flux Resources](https://github.com/yhagio/learn-react-flux)

## Requirements:
* You will need to have nodeJS installed.  You can get the latest version at http://nodejs.org/
* Once nodeJS is installed, install these modules globally: 
```
 $ sudo npm install -g gulp
 $ sudo npm install -g bower
```

## Install:
From the root project directory run these commands from the command line:
```
 $ npm install
 $ bower install
```

## Build

FOR SOME REASON THE MINIFIED FILES ARE NOT WORKING - INVESTIGATING . . .

* Navigate to app dir and `$ gulp --type production` in the cli.
 
This will build a browserfied, uglified version of main.js
while anything else will maintain a non uglified main.js file for easier debugging.

## Run
To run so you can modify react / flux files and they will get browserfied on the fly:
* In app dir `$ gulp watch`

This watcher is based on [Browserify](http://browserify.org/) and
[Watchify](https://github.com/substack/watchify), and it transforms
React's JSX syntax into standard JavaScript with [Reactify](https://github.com/andreypopp/reactify).

## Folder Structure of Stats Module Code

      gui/gui                             # actual ui code is stored here
            src/                          # editable source files
              js/                         # js files
                yourModuleName/                    # stats module
                  actions/                # flux actions
                  scripts/                # react components
                  constants/              # flux constants
                  views/                  # flux dispatcher
                  stores/                 # flux stores
                  yourModuleName.js       # main react component
            static/
              dist/
                yourModuleName.js                   # browserfied react / flux concat file
              js/
                bower_components/         # bower components
            templates/
              jinjaTemplateModuleFolder/
                jinjaTemplateModuleName.html   # jinja module template

