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

### Production
To have the app use the production configuration options (ie. production APIV2 endpoint host):

* Navigate to app dir and `$ gulp --type production` in the cli
 
FOR SOME REASON THE MINIFIED FILES ARE NOT WORKING - INVESTIGATING . . .
This will build a browserfied, uglified version of main.js
while anything else will maintain a non uglified main.js file for easier debugging.

### Development

* Navigate to app dir and `$ gulp --type development` in the cli

## Run
To run so you can modify react / flux files and they will get browserfied on the fly:
* In app dir `$ gulp watch --type development`

This watcher is based on [Browserify](http://browserify.org/) and it transforms
React's JSX syntax into standard JavaScript with [Reactify](https://github.com/andreypopp/reactify).

## Folder Structure of React / Flux GUI Module Code

      gui/gui                             # actual ui code is stored here
            src/                          # editable source files
              js/                         # js files
                common/                   # files used by multiple modules go here
                  commands/               # common api interfaces
                    auth_headers.js       # auth header api
                    base.js               # base command class
                  configs/                
                    development.js        # configs for development environment
                    LoadConfig.js         # reads a cli / gulp or environment variable to determine app environment
                    production.js         # configs for production environment 
                    qa.js                 # configs for qa environment 
                  constants/
                    Constants.js          # constants used by base app dispatcher
                  dispatcher/
                    AppDispatcher.js      # base app dispatcher
                  stores/
                    Store.js              # base store
                  utils/
                    APIUtils.js           # utilities for API classes
                yourModuleName/           # module
                  commands/               # interfaces for apis
                  actions/                # flux actions
                  scripts/                # react components
                  constants/              # flux constants
                  views/                  # flux dispatcher
                  stores/                 # flux stores
                  moduleName.js           # main react component
            static/
              dist/
                moduleName.js             # browserfied react / flux concat file
              js/
                bower_components/         # bower components
            templates/
              jinjaTemplateModuleFolder/
                jinjaTemplateModuleName.html   # jinja module template

