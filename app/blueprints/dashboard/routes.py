from . import bp

@bp.get("/")
def index():
    return "Vitaj v aplikacii osobneho rozpoctu"
