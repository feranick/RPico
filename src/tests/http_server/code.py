import socketpool
import wifi

from adafruit_httpserver import Server, Request, Response, GET, POST


pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, debug=True)


FORM_HTML_TEMPLATE = """
<html lang="en">
    <head>
        <title>Form with {enctype} enctype</title>
    </head>
    <body>
        <a href="/?run">
            <button>RUN CONTROL</button>
        </a><br />
        <a href="/?status">
            <button>STATUS</button>
        </a><br />
    </body>
</html>
"""


@server.route("/", [GET, POST])
def form(request: Request):
    """
    Serve a form with the given enctype, and display back the submitted value.
    """
    enctype = request.query_params.get("enctype", "text/plain")
    
    if request.method == GET:
        req = str(request.query_params)
        print("params:"+req)
        if req == "run=":
            print ("RUN")
        if req == "status=":
            print ("STATUS")
    
    if request.method == POST:
        posted_value = request.form_data.get("something")

    return Response(
        request,
        FORM_HTML_TEMPLATE.format(
            enctype=enctype,
            submitted_value=(
                f"<h3>Enctype: {enctype}</h3>\n<h3>Submitted form value: {posted_value}</h3>"
                if request.method == POST
                else ""
            ),
        ),
        content_type="text/html",
    )


server.serve_forever(str(wifi.radio.ipv4_address))
