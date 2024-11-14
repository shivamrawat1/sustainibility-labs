import replicate
import base64

input = {
    "prompt": "An illustration of a gold running shoe with the text \"Run AI with an API\" written on the shoe. The shoe is placed on a pink background. The text is white and bold. The overall image has a modern and techy vibe, with elements of speed."
}

output = replicate.run(
    "ideogram-ai/ideogram-v2-turbo",
    input=input
)

# Check and print the type of 'output'
print("Type of output:", type(output))

# If the output is a FileOutput object, retrieve the content
if isinstance(output, replicate.helpers.FileOutput):
    # Read the file content as bytes
    file_data = output.read()
    
    # Save the binary data to an image file
    with open("decoded_image.png", 'wb') as file:
        file.write(file_data)

    print("Image successfully decoded and saved as decoded_image.png")
else:
    print("Unexpected output type.")
