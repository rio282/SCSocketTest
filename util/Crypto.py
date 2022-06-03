import base64


def encrypt(tokens: [str]) -> [bytes]:
    for token in range(len(tokens)):
        tokens[token] = base64.b64encode(tokens[token].encode("ascii"))
    return tokens


def decrypt(tokens: [bytes]) -> [str]:
    for token in range(len(tokens)):
        tokens[token] = base64.b64decode(tokens[token])
    return tokens
