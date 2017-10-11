module.exports = function(grunt) {
  require('load-grunt-tasks')(grunt);

  var path = 'rer/groupware/notify/browser/static';
  var registry = 'rer/groupware/notify/profiles/default/registry.xml';

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    path: path,
    registry: registry,
    uglify: {
      options: {
        sourceMap: true,
        sourceMapName: '<%= path %>/groupwarenotify.js.map',
      },
      groupwarenotify: {
        files: {
          '<%= path %>/groupwarenotify.min.js': ['<%= path %>/groupwarenotify.js'],
        },
      },
    },
    xmlpoke: {
      updateDate: {
        options: {
          xpath: '/registry/records/value[@key = "last_compilation"]',
          value: grunt.template.today('yyyy-mm-dd HH:MM:00'),
        },
        files: {
          '<%= registry %>': '<%= registry %>',
        },
      },
    },
    watch: {
      groupwarenotify: {
        files: '<%= path %>/groupwarenotify.js',
        tasks: ['uglify:groupwarenotify', 'xmlpoke:updateDate'],
      },
    },
  });

  grunt.registerTask('default', ['watch']);
  grunt.registerTask('build', ['uglify:groupwarenotify', 'xmlpoke:updateDate']);
};
