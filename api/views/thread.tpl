<head>
<style>
a {
    text-decoration: none;
    color: rgb(51, 118, 164);
}
#body {
    margin-left: 4em;
    width: 700px;
    margin-right: 8em;
    font-size: 12pt;
}
pre {
    margin: 10px 35px 10px 0px;
    padding: 5px 10px;
    background-color: rgb(249, 249, 249);
    border-style: solid;
    border-width: 1px 0px;
    border-color: rgb(201, 201, 201);
}
.descriptions {
    background-color: #FFEEEE;
}
.description_value {
    margin-left: 2em;
}
.comment_user {
    margin-top: 1em;
    color: rgb(51, 118, 164);
}
.comment_text p {
    margin-top: .25em;
    margin-bottom: .5em;
}
.comment_embed {
    border-left: 3px solid rgb(219, 235, 248);
    padding-left: 10px;
    font-size: smaller;
}
</style>
<body>
<div id="body">
<h1><a target="_blank" href="{{ thread_html["link"] }}">{{!thread_html["title"] }}</a></h1>
<div class="descriptions">
% for description in thread_html["descriptions"]:
    <div class="description">
        <b>{{ description["name"] }}</b>:
        <div class="description_value">{{!description["value"] }}</div>
    </div>
% end
</div>
% for re in thread_html["res"]:
    <div class="comment">
    <div class="comment_user">{{ re["user"] }}</div>
    <div class="comment_text">{{!re["text"] }}</div>
%   if re["embed"]:
        <div class="comment_embed">
        <div class="comment_embed_title">{{ re["embed"]["title"] }}</div>
        <div class="comment_embed_text">{{ re["embed"]["description"] }}</div>
        </div>
%   end
    </div>
% end
</div>
