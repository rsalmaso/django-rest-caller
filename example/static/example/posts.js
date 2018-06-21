"use strict";

function get_json(name) {
  var el = document.getElementById(name);
  return JSON.parse(el.textContent || el.innerText);
}

new Vue({
  el: "#app",
  delimiters: ["${", "}"],
  data: function() {
    var posts = get_json("posts-data");
    return {
      panel: 'list',
      post: null,
      posts: posts.data
    }
  },
  watch: {
    'window.location.pathname': function(value) {
      console.log(value);
    }
  },
  created: function() {
    var self = this;
    var path = window.location.pathname;
    if (path === '/posts/') {
      // list view
      self.show_list();
    } else {
      // detail view
      path = path.replace('/posts/', '');
      this.posts.map(function(post, index) {
        if (post.slug === path) {
          self.show_detail(index);
        }
      });
    }

  },
  methods: {
    show_panel: function(panel, url) {
      this.panel = panel;
      history.pushState("", "", url);
    },
    show_list: function(ev) {
      if (ev) {ev.preventDefault();};
      this.post = null;
      this.show_panel("list", "/posts/");
    },
    show_detail: function(index, ev) {
      if (ev) {ev.preventDefault();};
      this.post = this.posts[index];
      this.show_panel("detail", "/posts/" + this.post.slug);
    }
  }
});
