# -*- coding: utf-8 -*-
import base64
import random

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, State
import functools

import math
from textgenrnn import textgenrnn
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

import pandas as pd

dropdown_files = pd.read_csv("dropdown_options.csv")
dropdown_df = dropdown_files.to_dict("records")
dropdown_list = list(dropdown_files['value'])

maxNumberOfPosterGenerationsPerQuery = 5
num_cashes_per_type_of_query = 1000

image_directory = 'static/'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

static_image_route = 'imgs/static/'


def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


app.layout = html.Div(
    [html.Div([html.H1("""Women's March Poster Generator"""), html.P("""Generate Posters! ---More info goes here""")],
              className="w3-container w3-blue w3-padding-48 w3-center"),
     html.Div([
         dcc.Slider(
             id='input-2-submit',
             min=0,
             max=1,
             step=0.05,
             value=.5,
             className="""w3-center"""),
         html.Div(id='slider-output-container', className="w3-margin-bottom"),
         html.Div(id='output-submit'),
         html.Button('Generate AI', id='ai-button'),
         html.Label("""OPTIONAL: Use the drop down to get an AI suggested text.""", className="w3-margin-top"),
         dcc.Dropdown(
             id='dropdown',
             options=[{
                 "label": "Women's Rights are Human Rights",
                 "value": "Women's Rights are Human Rights"
             }],
             clearable=False,
             placeholder="Select text", className="w3-margin-bottom"),
         html.Label("""Edit the text to generate the image!"""),

         dcc.Textarea(id='user-text-input', value='Choose text to place on the image',
                      style={'width': '100%'}, className="w3-margin-bottom"),
         html.Div(
             [html.Label("""Select an image for the poster generation."""),
              dcc.Dropdown(id="image-dropdown", options=dropdown_df, value=dropdown_list[0]),
              html.Div([html.Img(id='image_selection_preview', width="""10%""", height="auto"), ]), ],
             className="w3-margin-bottom"),
         html.Button('Generate image based on text', id='pic-button'), ],
         className="w3-container w3-margin w3-center"),
     html.Div(html.Img(id='image'), className="w3-card-4 w3-hover-shadow w3-margin w3-center"), ])


@app.callback(
    dash.dependencies.Output('image_selection_preview', 'src'),
    [dash.dependencies.Input('image-dropdown', 'value')])
def update_image_src(value):
    if value not in dropdown_list:
        raise Exception('"{}" is excluded from the allowed static files'.format(value))
    encoded_image = base64.b64encode(open(static_image_route + value, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded_image.decode())


@functools.lru_cache(maxsize=32)
def slow_function():
    textgen_2 = textgenrnn('textgenrnn_weights.hdf5')
    return textgen_2


@functools.lru_cache(maxsize=num_cashes_per_type_of_query * 10)
def textGen(numGen, temperature, randomState, return_as_list=True):
    del randomState
    textgen_2 = slow_function()
    out = textgen_2.generate(numGen, temperature=temperature, return_as_list=return_as_list)
    textgen_2 = None
    return out


# Dash CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

# Loading screen CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

# W3 CSS
app.css.append_css({"external_url": "https://www.w3schools.com/w3css/4/w3.css"})


@app.callback([Output("dropdown", "options")],
              [dash.dependencies.Input('ai-button', 'n_clicks'), ],
              [State('input-2-submit', 'value')])
def update_output(ns1, input2):
    numGen = maxNumberOfPosterGenerationsPerQuery
    intTemp = max(0, min(1, float(input2)))
    out = (textGen(numGen, temperature=intTemp, randomState=random.randint(1, num_cashes_per_type_of_query),
                   return_as_list=True))

    return [[{'label': val, 'value': val} for val in out]]


@app.callback(
    dash.dependencies.Output('slider-output-container', 'children'),
    [dash.dependencies.Input('input-2-submit', 'value')])
def update_output(value):
    return '"AI" creativity slider set to {} percent'.format(value * 100)


@app.callback(
    dash.dependencies.Output('user-text-input', 'value'),
    [dash.dependencies.Input('dropdown', 'value')])
def update_output(value):
    return value


def split_lines(sentence):
    words = sentence.split()
    split_space = math.ceil(len(words) / 2)
    return " ".join(words[:split_space]), " ".join(words[split_space:])


def make_the_image(str, img_file):
    topString, bottomString = split_lines(str)

    filename = static_image_route + img_file

    # TODO do not do random ints and generate better file names
    outputFileName = "imgs/generated/{}_temp{}.jpg".format(img_file, random.randint(1, 999999999999))

    img = Image.open(filename)
    imageSize = img.size
    fontLocation = "Gaegu/Gaegu-Bold.ttf"

    # find biggest font size that works
    fontSize = int(imageSize[1] / 5)
    font = ImageFont.truetype(fontLocation, fontSize)
    topTextSize = font.getsize(topString)
    bottomTextSize = font.getsize(bottomString)
    while topTextSize[0] > imageSize[0] - 20 or bottomTextSize[0] > imageSize[0] - 20:
        fontSize = fontSize - 1
        font = ImageFont.truetype(fontLocation, fontSize)
        topTextSize = font.getsize(topString)
        bottomTextSize = font.getsize(bottomString)

    # find top centered position for top text
    topTextPositionX = (imageSize[0] / 2) - (topTextSize[0] / 2)
    topTextPositionY = 0
    topTextPosition = (topTextPositionX, topTextPositionY)

    # find bottom centered position for bottom text
    bottomTextPositionX = (imageSize[0] / 2) - (bottomTextSize[0] / 2)
    bottomTextPositionY = imageSize[1] - bottomTextSize[1]
    bottomTextPosition = (bottomTextPositionX, bottomTextPositionY)

    draw = ImageDraw.Draw(img)

    # draw outlines
    # there may be a better way
    outlineRange = int(fontSize / 15)
    for x in range(-outlineRange, outlineRange + 1):
        for y in range(-outlineRange, outlineRange + 1):
            draw.text((topTextPosition[0] + x, topTextPosition[1] + y), topString, (0, 0, 0), font=font)
            draw.text((bottomTextPosition[0] + x, bottomTextPosition[1] + y), bottomString, (0, 0, 0), font=font)

    draw.text(topTextPosition, topString, (255, 255, 255), font=font)
    draw.text(bottomTextPosition, bottomString, (255, 255, 255), font=font)

    img.save(outputFileName)

    return outputFileName


@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('pic-button', 'n_clicks')],
    [State(component_id='user-text-input', component_property='value'),
     State(component_id='image-dropdown', component_property='value')])
def update_image_src(n_clicks, str, file_name):
    # print the image_path to confirm the selection is as expected
    if str == None:
        str = "TEXT WILL GO HERE"
    output_file = make_the_image(str, file_name)
    encoded_image = base64.b64encode(open(output_file, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded_image.decode())


if __name__ == '__main__':
    app.run_server(debug=True)
