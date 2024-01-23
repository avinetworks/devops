/* global shave Headroom WOW */

(function($) {
  ///////////////////////////////////////////////////////////////////
  //
  // Main Menu
  //
  ///////////////////////////////////////////////////////////////////

  // Main Menu - Mobile Dropdown
  ///////////////////////////////////////////////////////////////////

  $('.menu-item-has-children').on('click', function() {
    var openClass = 'sub-menu-is-open';
    var $this = $(this);
    var alreadyOpen = false;

    if ($this.hasClass(openClass)) {
      alreadyOpen = true;
    }

    $('.menu-item-has-children').removeClass(openClass);

    if (!alreadyOpen) {
      $this.addClass(openClass);
    }
  });

  // Main Menu - Mobile Open/Close

  $('.js-nav-toggle').on('click', function() {
    $('#menu-main-menu').toggleClass('menu--is-open');
  });

  $(window).on('resize', function() {
    if (window.matchMedia('(min-width: 901px)').matches) {
      $('#menu-main-menu').removeClass('menu--is-open');
    }
  });

  ///////////////////////////////////////////////////////////////////
  //
  // Mini Nav
  //
  ///////////////////////////////////////////////////////////////////

  // Mini Nav - Dropdown Location Helper
  ///////////////////////////////////////////////////////////////////

  $('.js-mini-nav select')
    .find('option[value="' + window.location.pathname.replace(/\/$/, '') + '"]')
    .attr('selected', 'selected');

  $('.js-mini-nav select').change(function() {
    window.location = $(this)
      .find('option:selected')
      .val();
  });


  $('.js-mini-nav-link').each(function() {
    var $this = $(this);
    var activeClass = 'mini-nav__link--is-active';

    if (
      $this.attr('href') === window.location.pathname ||
      $this.attr('href') === window.location.pathname.slice(0, -1)
    ) {
      $this.addClass(activeClass);
    }
  });

  ///////////////////////////////////////////////////////////////////
  //
  // Slider (flickity)
  //
  ///////////////////////////////////////////////////////////////////

  if ($('.js-slider').length) {
    $('.js-slider').flickity({
      // options
      cellSelector: '.js-slide',
      cellAlign: 'center',
      wrapAround: true,
      autoPlay: 6500,
      pageDots: true,
      prevNextButtons: false,
      contain: true
    });

    setTimeout(function() {
      $('.js-slider').flickity('resize');
    }, 550);
  }

  if ($('.js-brand-slider').length) {
    $('.js-brand-slider').flickity({
      // options
      cellSelector: '.js-slide',
      cellAlign: 'center',
      wrapAround: true,
      imagesLoaded: true,
      autoPlay: 3500,
      pageDots: false,
      prevNextButtons: false
    });
  }

  if ($('.js-content-slider').length) {
    $('.js-content-slider').flickity({
      // options
      cellSelector: '.js-slide',
      cellAlign: 'center',
      wrapAround: true,
      imagesLoaded: true,
      autoPlay: 8000,
      pageDots: true,
      prevNextButtons: false
    });
  }

  if ($('.js-hero-slider').length) {
    $('.js-hero-slider').flickity({
      // options
      cellSelector: '.js-slide',
      cellAlign: 'center',
      wrapAround: true,
      autoPlay: 8000,
      pageDots: true,
      prevNextButtons: false,
      draggable: true
    });
  }

  if ($('.js-fancy-hero-slider').length) {
    $('.js-fancy-hero-slider').flickity({
      // options
      cellSelector: '.js-slide',
      cellAlign: 'center',
      wrapAround: true,
      autoPlay: 4000,
      pageDots: true,
      imagesLoaded: true,
      prevNextButtons: true,
      draggable: false
    });
  }

  if ($('.js-macbook-slider').length) {
    $('.js-macbook-slider').flickity({
      // options
      cellSelector: '.js-slide',
      cellAlign: 'center',
      wrapAround: true,
      imagesLoaded: true,
      autoPlay: 6500,
      pauseAutoPlayOnHover: false,
      pageDots: false,
      prevNextButtons: false
    });

    $('.js-macbook-slider').on('select.flickity', function() {
      var flkty = $('.js-macbook-slider').data('flickity');
      var curSlide = parseInt(flkty.selectedIndex, 10);
      var marks = $('[class*=js-mark]');
      var markClass = 'mark';

      marks.removeClass(markClass);

      $('.js-mark--' + (curSlide + 1)).addClass(markClass);
    });
  }

  if ($('.js-quote-slider').length) {
    $('.js-quote-slider').flickity({
      // options
      cellSelector: '.js-slide',
      cellAlign: 'center',
      wrapAround: true,
      autoPlay: 6500,
      prevNextButtons: false
    });
  }
  //////////////////////////////////////////////////////////////////////////////
  //
  // Scroll Nav Animations
  //
  //////////////////////////////////////////////////////////////////////////////

  // grab an element
  const topNav = document.querySelector('.js-top-nav');

  // construct an instance of Headroom, passing the element
  const headroom = new Headroom(topNav, {
    classes: {
      // when element is initialised
      initial: 'headroom',
      // when scrolling up
      pinned: 'top-nav--pinned',
      // when scrolling down
      unpinned: 'top-nav--unpinned',
      // when above offset
      top: 'top-nav--top',
      // when below offset
      notTop: 'top-nav--not-top',
      // when at bottom of scoll area
      bottom: 'top-nav--bottom',
      // when not at bottom of scroll area
      notBottom: 'top-nav--not-bottom'
    }
  });

  // initialise
  headroom.init();

  //////////////////////////////////////////////////////////////////////////////
  //
  // Smooth Scroll Anchor Links
  //
  //////////////////////////////////////////////////////////////////////////////

  $('body').on('click', 'a[href*=\\#]:not([href=\\#])', function() {
    var target = $(this.hash);

    // Check if link is internal
    if (
      location.pathname.replace(/^\//, '') ===
        this.pathname.replace(/^\//, '') ||
      location.hostname === this.hostname
    ) {
      target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');

      if (target.length) {
        $('html,body')
          .animate(
            {
              scrollTop: target.offset().top - 85 // Offset amount is used to compensate for sticky nav
            },
            750
          )
          .trigger('scroll');

        // return false;
      }
    }
  });

  //////////////////////////////////////////////////////////////////////////////
  //
  // Match Heights
  //
  //////////////////////////////////////////////////////////////////////////////

  $('.js-match-all-g1').matchHeight(false);
  $('.js-match-all-g2').matchHeight(false);
  $('.js-match-across').matchHeight();
  $('.js-match-slide').matchHeight(false);

  //////////////////////////////////////////////////////////////////////////////
  //
  // Popups
  //
  //////////////////////////////////////////////////////////////////////////////

  $('.js-popup').magnificPopup({ type: 'iframe' });
  $('.js-img-popup').magnificPopup({
    type: 'image',
    image: {
      verticalFit: true
    }
  });

  $('.js-content-modal').magnificPopup({
    type: 'inline',
    preloader: false,
    focus: '#name',

    // When elemened is focused, some mobile browsers in some cases zoom in
    // It looks not nice, so we disable it:
    callbacks: {
      beforeOpen: function() {
        if ($(window).width() < 700) {
          this.st.focus = false;
        } else {
          this.st.focus = '#name';
        }
      }
    }
  });

  //////////////////////////////////////////////////////////////////////////////
  //
  // Shave
  //
  //////////////////////////////////////////////////////////////////////////////

  shave('.js-bio', 100);

  $('.js-read-more').on('click', function() {
    var $this = $(this);
    var target = $this.parent().find('.js-bio');
    var targetShave = target.find('.js-shave');
    var targetShaveChar = target.find('.js-shave-char');

    $(targetShave).toggle();
    $(targetShaveChar).toggleClass('hide-shave');
  });

  //////////////////////////////////////////////////////////////////////////////
  //
  // Play Video on Scroll
  //
  //////////////////////////////////////////////////////////////////////////////

  // jQuery(function() {
  //   /**
  //    * Take appear or disappear callbacks.
  //    */

  //   $('.js-scroll-video').peekaboo(
  //     function() {
  //       // on appear callback
  //       $(this)[0].play();
  //     },
  //     function() {
  //       // on disappear callback
  //       // $(this)[0].pause();
  //     }
  //   );
  // });

  //////////////////////////////////////////////////////////////////////////////
  //
  // Partners
  //
  //////////////////////////////////////////////////////////////////////////////

  $('.js-partner').on('click', function() {
    var $this = $(this);
    var activeClass = 'partner-grid__item--is-expanded';
    var isOpen = false;

    if ($this.hasClass(activeClass)) {
      isOpen = true;
    }

    $('.js-partner').removeClass(activeClass);

    if (isOpen === false) {
      $this.addClass(activeClass);
    }
  });

  // Open the first one by defualt
  $('.js-partner:first-child').trigger('click');

  //////////////////////////////////////////////////////////////////////////////
  //
  // Forms
  //
  //////////////////////////////////////////////////////////////////////////////

  $('.search-form').submit(function() {
    // Prevent users from clicking submitting the search Form as it should
    // only be used for its linked fuzzy matched predictions/suggestions
    return false;
  });

  //////////////////////////////////////////////////////////////////////////////
  //
  // Resources
  //
  //////////////////////////////////////////////////////////////////////////////

  // Hide additional resources by defualt
  $('.js-resource-expand')
    .parent()
    .find('.js-extra-resources')
    .hide();

  // On click of and expand/collapse toggle
  $('.js-resource-expand').on('click', function(e) {
    var $this = $(this);
    var parent = $this.parent();
    var button = parent.find('.js-resource-expand--button');
    var moreResources = parent.find('.js-extra-resources');
    var showText = '+ Show More';
    var hideText = '- Hide';

    e.preventDefault();

    // Expand/collapse additional resources
    if (moreResources.is(':visible')) {
      moreResources.hide();
    } else {
      moreResources.css({
        display: 'block'
      });
    }

    // Toggle the expand/collapse text
    if (button.text() === showText) {
      button.text(hideText);
    } else {
      button.text(showText);
    }
  });

  //////////////////////////////////////////////////////////////////////////////
  //
  // Comparison Table
  //
  //////////////////////////////////////////////////////////////////////////////

  // Table collapsing
  function toggleCompareGroup(group) {
    var compareGroup = $('.js-compare-group-' + group);

    compareGroup.each(function() {
      $(this).toggle();
    });
  }

  function toggleCompareGroupIndicator(el) {
    var collapseClass = 'comparison-chart__cell--section--is-closed';

    el.toggleClass(collapseClass);
  }

  $('.js-compare-group-toggle').on('click', function() {
    var $this = $(this);
    var group = $this.attr('data-compare-group');

    toggleCompareGroupIndicator($this);
    toggleCompareGroup(group);
  });

  // Filtering
  function unfilter(hiddenClass) {
    $('[data-type]').removeClass(hiddenClass);
  }

  function filter(filterType, hiddenClass) {
    $('[data-type=' + filterType + ']').addClass(hiddenClass);
  }

  $('.js-compare-filter-control').on('change', function() {
    var filterType = $('.js-compare-filter-control:checked').val();
    var hideClass = 'comparison-chart__cell--is-hidden';

    unfilter(hideClass);

    if (filterType !== 'none') {
      filter(filterType, hideClass);
    }
  });

  //////////////////////////////////////////////////////////////////////////////
  //
  // Wow
  //
  //////////////////////////////////////////////////////////////////////////////

  new WOW().init();

  //////////////////////////////////////////////////////////////////////////////
  //
  // Tabs
  //
  //////////////////////////////////////////////////////////////////////////////

  // Create tabs from panels
  $('.js-tab-panel').each(function() {
    var $this = $(this);
    var title = $this.attr('data-title');
    var bg = $this.attr('data-bg');
    var sectionTitle = $this.attr('data-section-title');
    var target = $this.attr('id');
    var tabGroup = $this.parent().find('.js-tab-group');
    var tabButton =
      '<button class="tab-group__tab js-tab" data-target="' +
      target +
      '" data-bg="' +
      bg +
      '" data-section-title="' +
      sectionTitle +
      '">' +
      title +
      '</button>';

    tabGroup.append(tabButton);
  });

  // Click handler
  $('.js-tab').on('click', function() {
    var $this = $(this);
    var tabGroup = $this.parent();
    var target = $this.attr('data-target');
    var bg = $this.attr('data-bg');
    var sectionTitle = $this.attr('data-section-title');
    var tabActiveClass = 'tab-group__tab--is-active';
    var panelActiveClass = 'tab-group__panel--is-active';

    // Apply background image and Update the title
    tabGroup
      .parent()
      .parent()
      .css({ 'background-image': 'url(' + bg + ')' })
      .find('.js-tab-section-title')
      .html(sectionTitle);
    // Deactivate all sibling tabs
    tabGroup.find('.js-tab').removeClass(tabActiveClass);
    // Reactivate this tab
    $this.addClass(tabActiveClass);
    // Deactivate all sibling panels
    tabGroup.siblings('.js-tab-panel').removeClass(panelActiveClass);
    // Reactivate this panel
    $('#' + target).addClass(panelActiveClass);
  });

  $('.tab-group .js-tab:first-child').trigger('click');

  //////////////////////////////////////////////////////////////////////////////
  //
  // Tabs 2
  //
  //////////////////////////////////////////////////////////////////////////////

  // Create tabs from panels
  $('.js-tab-panel-2').each(function() {
    var $this = $(this);
    var title = $this.attr('data-title');
    var bg = $this.attr('data-bg');
    var sectionTitle = $this.attr('data-section-title');
    var target = $this.attr('id');
    var tabGroup = $this.parent().find('.js-tab-group-2 .js-tab-wrap');
    var tabButton =
      '<button class="tab-group-2__tab js-tab-2" data-target="' +
      target +
      '" data-bg="' +
      bg +
      '" data-section-title="' +
      sectionTitle +
      '">' +
      title +
      '</button>';

    tabGroup.append(tabButton);
  });

  // Click handler
  $('.js-tab-2').on('click', function() {
    var $this = $(this);
    var tabGroup = $this.parent();
    var target = $this.attr('data-target');
    var bg = $this.attr('data-bg');
    var sectionTitle = $this.attr('data-section-title');
    var tabActiveClass = 'tab-group-2__tab--is-active';
    var panelActiveClass = 'tab-group-2__panel--is-active';

    // Apply background image and Update the title
    tabGroup
      .parent()
      .parent()
      .css({ 'background-image': 'url(' + bg + ')' })
      .find('.js-tab-section-title')
      .html(sectionTitle);
    // Deactivate all sibling tabs
    tabGroup.find('.js-tab-2').removeClass(tabActiveClass);
    // Reactivate this tab
    $this.addClass(tabActiveClass);
    // Deactivate all sibling panels
    tabGroup.parent().siblings('.js-tab-panel-2').removeClass(panelActiveClass);
    // Reactivate this panel
    $('#' + target).addClass(panelActiveClass);
  });

  $('.js-tab-wrap .js-tab-2:first-child').trigger('click');

  //////////////////////////////////////////////////////////////////////////////
  //
  // Tabs 3
  //
  //////////////////////////////////////////////////////////////////////////////

  // Create tabs from panels
  $('.js-tab-panel-3').each(function() {
    var $this = $(this);
    var title = $this.attr('data-title');
    var sectionTitle = $this.attr('data-section-title');
    var target = $this.attr('id');
    var tabGroup = $this.parent().find('.js-tab-group-3 .js-tab-wrap-3');
    var tabButton =
      '<button class="tab-group-3__tab js-tab-3" data-target="' +
      target +
      '" data-section-title="' +
      sectionTitle +
      '">' +
      title +
      '</button>';

    tabGroup.append(tabButton);
  });

  // Click handler
  $('.js-tab-3').on('click', function() {
    var $this = $(this);
    var tabGroup = $this.parent();
    var target = $this.attr('data-target');
    var sectionTitle = $this.attr('data-section-title');
    var tabActiveClass = 'tab-group-3__tab--is-active';
    var panelActiveClass = 'tab-group-3__panel--is-active';

    // Apply background image and Update the title
    tabGroup
      .parent()
      .parent()
      .find('.js-tab-section-title')
      .html(sectionTitle);
    // Deactivate all sibling tabs
    tabGroup.find('.js-tab-3').removeClass(tabActiveClass);
    // Reactivate this tab
    $this.addClass(tabActiveClass);
    // Deactivate all sibling panels
    tabGroup.parent().siblings('.js-tab-panel-3').removeClass(panelActiveClass);
    // Reactivate this panel
    $('#' + target).addClass(panelActiveClass);
  });

  $(".js-tab-group-3 .js-tab-3:first-child").trigger("click");

  //////////////////////////////////////////////////////////////////////////////
  //
  // Feature List
  //
  //////////////////////////////////////////////////////////////////////////////

  $('.js-icon-tab').on('click', function() {
    var $this = $(this);
    var target = $this.attr('data-target');
    var tabActiveClass = 'icon-tab--is-active';
    var panelActiveClass = 'icon-tabs__panel--is-active';

    // Clear active states from tabs and panels
    $('.js-icon-tab').removeClass(tabActiveClass);
    $('.js-icon-tab-panel').removeClass(panelActiveClass);

    // Activate tab and panel
    $this.addClass(tabActiveClass);
    $('#' + target).addClass(panelActiveClass);
  });

  //////////////////////////////////////////////////////////////////////////////
  //
  // Feature List
  //
  //////////////////////////////////////////////////////////////////////////////

  // TODO: If this remains disabled, delete this, its CSS and its HTML hook
  // during the next clean up.

  // $('.js-feature-item').each(function() {
  //   var destination = $('.js-feature-jump-links');
  //   var $this = $(this);
  //   var title = $this.attr('data-title');
  //   var icon = $this.attr('data-icon');
  //   var id = $this.attr('id');

  //   destination.append(
  //     '<a class="feature-list__jump-link card jump-card" href="#' +
  //       id +
  //       '">' +
  //       '<img class="jump-card__icon" src="' +
  //       icon +
  //       '" alt="">' +
  //       '<div class="jump-card__title">' +
  //       title +
  //       '</div>' +
  //       '</a>'
  //   );
  // });

  //////////////////////////////////////////////////////////////////////////////
  //
  // Floating Button Fade In
  //
  //////////////////////////////////////////////////////////////////////////////

  if ($('.floating-buttons').length) {
    if (window.location.pathname === '/') {
      const buttonsHiddenClass = 'floating-buttons--are-hidden';

      $('.floating-buttons').addClass(buttonsHiddenClass);

      $(window).on('scroll', function() {
        if ($(window).scrollTop() >= 510) {
          $('.floating-buttons').removeClass(buttonsHiddenClass);
        } else if ($(window).scrollTop() < 510) {
          $('.floating-buttons').addClass(buttonsHiddenClass);
        }
      });
    }
  }

  //////////////////////////////////////////////////////////////////////////////
  //
  // Basic Content Images
  //
  //////////////////////////////////////////////////////////////////////////////

  if ($('.basic-content__body ').length) {
    $('.basic-content__body p img').unwrap();
  }

  //////////////////////////////////////////////////////////////////////////////
  //
  // Add class to hero that comes before mini-navs
  //
  //////////////////////////////////////////////////////////////////////////////

  $('.section--mini-nav')
    .prev()
    .addClass('hero-v2--with-subnav');
})(jQuery);