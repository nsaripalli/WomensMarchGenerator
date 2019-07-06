# -*- coding: utf-8 -*-
import base64
import os
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
number_of_images = len(dropdown_files) - 1
dropdown_df = dropdown_files.to_dict("records")
dropdown_options = list(dropdown_files['value'])


maxNumberOfPosterGenerationsPerQuery = 5
num_cashes_per_type_of_query = 1000

image_directory = 'static/'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',
                        'https://codepen.io/chriddyp/pen/brPBPO.css',
                        'https://www.w3schools.com/w3css/4/w3.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Art of the March Generator'
server = app.server

static_image_route = 'imgs/static/'

app.layout = html.Div(
    [html.Div([html.H1("""Art of the March Generator"""),
               html.P("""This is an experimental "AI" that generates women's march posters.""")],
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
              dcc.Slider(id="image-slider", min=0, max=number_of_images, step=1, value=43),
              html.Div(id='image-slider-output', className="w3-margin-bottom"),
              html.Div([html.Img(id='image_selection_preview', width="""10%""", height="auto"), ]), ],
             className="w3-margin-bottom"),
         html.Button('Generate image based on text',
                     id='pic-button',
                     className="""w3-button;
                                  w3-blue""",
                     style={'width': '562px', 'height': '52px'}), ],
         className="w3-container w3-margin w3-center"),
     html.Div(html.Img(id='image'), className="w3-card-4 w3-hover-shadow w3-margin w3-center"), ])


@app.callback(
    dash.dependencies.Output('image_selection_preview', 'src'),
    [dash.dependencies.Input('image-slider', 'value')])
def update_image_src(value):
    image_df = dropdown_files.iloc[value]
    # image_file_name = image_df['label']
    image_file_path = image_df['value']

    if image_file_path not in dropdown_options:
        raise Exception('"{}" is excluded from the allowed static files'.format(value))
    encoded_image = base64.b64encode(open(static_image_route + image_file_path, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded_image.decode())

@app.callback(
    dash.dependencies.Output('image-slider-output', 'children'),
    [dash.dependencies.Input('image-slider', 'value')])
def update_ai_creativity_to_user(value):
    image_df = dropdown_files.iloc[value]
    return image_df['label']

@functools.lru_cache()
def get_textgenn():
    textgen_2 = textgenrnn('textgenrnn_weights.hdf5')
    return textgen_2


@functools.lru_cache(maxsize=num_cashes_per_type_of_query * 10)
def generate_text(numGen, temperature, randomState, return_as_list=True):
    del randomState
    textgen_2 = get_textgenn()
    out = textgen_2.generate(numGen, temperature=temperature, return_as_list=return_as_list)
    return out


@app.callback([Output("dropdown", "options")],
              [dash.dependencies.Input('ai-button', 'n_clicks'), ],
              [State('input-2-submit', 'value')])
def update_output(ns1, input2):
    numGen = maxNumberOfPosterGenerationsPerQuery
    intTemp = max(0, min(1, float(input2)))
    out = (generate_text(numGen, temperature=intTemp, randomState=random.randint(1, num_cashes_per_type_of_query),
                         return_as_list=True))

    return [[{'label': val, 'value': val} for val in out]]


@app.callback(
    dash.dependencies.Output('slider-output-container', 'children'),
    [dash.dependencies.Input('input-2-submit', 'value')])
def update_ai_creativity_to_user(value):
    return '"AI" creativity slider set to {} percent'.format(value * 100)


@app.callback(
    dash.dependencies.Output('user-text-input', 'value'),
    [dash.dependencies.Input('dropdown', 'value')])
def selected_text_in_dropdown(value):
    return value


def split_lines(sentence):
    words = sentence.split()
    split_space = math.ceil(len(words) / 2)
    return " ".join(words[:split_space]), " ".join(words[split_space:])


def make_the_image(str, img_file):
    """Largly inspired by https://github.com/danieldiekmeier/memegenerator/blob/master/memegenerator.py"""
    # Heroku requires generated files to be under tmp.
    os.makedirs("/tmp/imgs/generated/", exist_ok=True)

    topString, bottomString = split_lines(str)

    filename = static_image_route + img_file

    # TODO do not do random ints
    # TODO use pathlib instead
    outputFileName = "/tmp/imgs/generated/{}_temp{}.jpg".format(img_file.split(".")[0], random.randint(1, 999999999999))

    img = Image.open(filename)
    imageSize = img.size
    fontLocation = "Open_Sans/OpenSans-ExtraBold.ttf"

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
     State(component_id='image-slider', component_property='value')])
def update_image_src(n_clicks, str, value):
    if str == None:
        str = "TEXT WILL GO HERE"
    output_file = make_the_image(str,  dropdown_files.iloc[value]['value'])
    encoded_image = base64.b64encode(open(output_file, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded_image.decode())

if __name__ == '__main__':
    app.run_server(debug=True)