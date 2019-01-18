def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('gallery_home', '/')
    config.add_route('gallery_list', '/gallery/list')
    config.add_route('gallery_save', '/gallery/save')
    config.add_route('gallery_invite_user', '/gallery/user/invite')
    config.add_route('gallery_detail', '/gallery/{id}')
    config.add_route('gallery_detail_json', '/gallery/json/{id}')
    config.add_route('gallery_save_photo', '/gallery/photo/save')
    config.add_route('gallery_like_photo', '/gallery/photo/like')
    config.add_route('gallery_update_review_status', '/gallery/photo/review')

