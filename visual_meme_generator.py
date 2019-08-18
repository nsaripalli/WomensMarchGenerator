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

num_cashes_per_type_of_query = 1000

image_directory = 'static/'

app = dash.Dash(__name__,
                meta_tags=[{
                    'name': 'viewport',
                    'content': 'width=device-width, initial-scale=1'
                },
                    {
                        'name': 'Art of the March Poster Generator',
                        'content': """Creates Women's March posters using \"AI\""""
                    }
                ])

app.title = 'Art of the March Generator'
server = app.server

static_image_route = 'imgs/static/'

app.layout = html.Div(
    [html.Div([html.H1("""Art of the March Generator""", style={'font-size': "-webkit-xxx-large"}),
               html.P("""This is an experimental "AI" that generates women's march posters.""")],
              className="w3-container w3-blue w3-padding-32 w3-center"),
     html.Div([html.Div([
         dcc.Slider(
             id='creativity-slider',
             min=0,
             max=1,
             step=0.05,
             value=.5,
             className="""w3-center"""),
         html.Div(id='slider-output-container', className="w3-margin-bottom"),
         html.Div(id='output-submit'),
         html.Button('Generate AI', id='generate-ai-button', className="w3-margin-bottom"),
         html.Label("""Edit the text to generate the image!"""),

         dcc.Textarea(id='user-text-input', value='Choose text to place on the image',
                      className="w3-margin-bottom"),
         html.Div(
             [html.Label("""Select an image for the poster generation by moving the slider below."""),
              dcc.Slider(id="image-slider", min=0, max=number_of_images, step=1, value=43),
              html.Div(id='image-slider-output', className="w3-margin-bottom"),
              html.Div([html.Img(id='image-selection-preview'), ]), ],
             className="w3-margin-bottom"),

         html.Button('Generate image based on text',
                     id='pic-button',
                     className="""w3-button;
                                  w3-blue""", ), ],

         className="larger column, w3-container w3-margin w3-center"),
         html.Div(html.Img(id='final-image'),
                  className="smaller column w3-card-4 w3-hover-shadow w3-margin"), ],
         className="row")], )  # w3-card-4 w3-hover-shadow w3-margin w3-center


@app.callback(
    dash.dependencies.Output('image-selection-preview', 'src'),
    [dash.dependencies.Input('image-slider', 'value')])
def update_image_src(value):
    image_df = dropdown_files.iloc[value]
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


def generate_text(numGen, temperature, return_as_list=True):
    textgen_2 = get_textgenn()
    out = textgen_2.generate(numGen, temperature=temperature, return_as_list=return_as_list)
    return out


@app.callback([Output("user-text-input", "value")],
              [dash.dependencies.Input('generate-ai-button', 'n_clicks'), ],
              [State('creativity-slider', 'value')])
def update_output(ns1, input2):
    temperature_within_bounderies = max(0, min(1, float(input2)))
    out = generate_text(1, temperature=temperature_within_bounderies)

    return out


@app.callback(
    dash.dependencies.Output('slider-output-container', 'children'),
    [dash.dependencies.Input('creativity-slider', 'value')])
def update_ai_creativity_to_user(value):
    return '"AI" creativity slider set to {} percent'.format(value * 100)


def split_lines(sentence):
    words = sentence.split()
    split_space = math.ceil(len(words) / 2)
    return " ".join(words[:split_space]), " ".join(words[split_space:])


def make_the_image(str, img_file):
    """Largly inspired by https://github.com/danieldiekmeier/memegenerator/blob/master/memegenerator.py"""
    # Heroku requires generated files to be under tmp.
    os.makedirs("/tmp/imgs/generated/", exist_ok=True)

    name, ext = os.path.splitext(img_file)
    outputFileName = "/tmp/imgs/generated/{}_temp{}.{}".format(name, hash(str), ext)

    if not os.path.isfile(outputFileName):
        topString, bottomString = split_lines(str)

        filename = static_image_route + img_file

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
    dash.dependencies.Output('final-image', 'src'),
    [dash.dependencies.Input('pic-button', 'n_clicks')],
    [State(component_id='user-text-input', component_property='value'),
     State(component_id='image-slider', component_property='value')])
def update_image_src(n_clicks, str, value):
    if str == None:
        str = "TEXT WILL GO HERE"

    output_file = make_the_image(str, dropdown_files.iloc[value]['value'])
    encoded_image = base64.b64encode(open(output_file, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded_image.decode())


if __name__ == '__main__':
    app.run_server(debug=True)
