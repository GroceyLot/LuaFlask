# LuaFlask documentation

## Introduction

This documentation provides guidance on using `.lua` and `.shtml` files in your Flask application, how to handle errors gracefully, and how to utilize the provided API features. The application leverages Lupa for executing Lua scripts, allowing seamless integration of server-side scripting within HTML.

## Lua File Usage

Lua files are located in the `routes` directory of your application. Each Lua file should have a naming convention of `_.lua` within a subdirectory, or simply be named after the path if it is a direct route.

### Creating a Lua File

- **Location**: `routes/{subpath}/_.lua` or `routes/{subpath}.lua`
- **Example**:
  ```lua
  return function(requestData)
      local response = {
          response = "Hello from Lua!",
          type = "text/plain",
          code = 200
      }
      return response
  end
  ```

### Accessing Request Data

Inside your Lua script, you can access request data using the `requestData` parameter, which includes:

- `urlArguments`: A table containing query parameters.
- `headers`: A table containing HTTP headers.
- `method`: The HTTP method (GET, POST, etc.).

### Executing a Lua File

When a request is made to the server, the appropriate Lua file is executed based on the requested path. The application will return the response defined in the Lua file.

## SHTML File Usage

SHTML files allow you to embed Lua code directly within HTML using special tags. The file extension must be `.shtml`.

### Creating an SHTML File

- **Location**: `routes/{subpath}.shtmlq`
- **Example**:
  ```html
  <html>
  <head>
      <title>My SHTML Page</title>
  </head>
  <body>
      <h1>Welcome to My SHTML Page!</h1>
      <$lua>
      function greet()
          return "Hello from embedded Lua!"
      end
      return greet()
      <$>
  </body>
  </html>
  ```

### Processing Lua Tags

Any Lua code enclosed in `<$lua ... $>` tags will be executed, and its output will replace the tag in the HTML response. Ensure proper error handling within Lua to avoid disrupting the HTML structure. If there is an error, it will be filled with `<div class="_error">Error</div>` (if you are on a development server it will show the error message)


## Error Handling

The application provides a robust error-handling mechanism that serves custom error pages or plain text responses for various HTTP error codes.

### Custom Error Pages

Custom error pages can be created in the `routes/errors` directory with corresponding filenames such as:

- `404.html` for Not Found errors.
- `500.html` for Internal Server errors.
- `luaError.html` specifically for Lua execution errors.
  - In this one, you can put a `<$error$>` tag to be filled in with the error message (if you aren't on a development server it will just say 'Error')

### Serving Error Pages

When an error occurs, the application attempts to serve the appropriate error page:

1. If a Lua error occurs, it will first try to serve `luaError.html`.
2. If that fails, it will attempt to serve `500.html`.
3. If neither file exists, a plain text response "Error 500" will be returned.

### 404 Handling

If a requested route or file does not exist, a `404.html` page will be served.


## API Function Access

### HttpApi

- `api.http.get(host, path, headers=None)`: Sends a GET request to the specified host and path.
- `api.http.post(host, path, body, headers=None)`: Sends a POST request to the specified host and path.

### JsonApi

- `api.json.encode(data)`: Encodes a Python dictionary to a JSON string.
- `api.json.encodeArray(data)`: Encodes a Python list to a JSON string.
- `api.json.decode(data)`: Decodes a JSON string into a Lua table.

### OsApi

- `api.os.listDir(path)`: Lists the contents of the specified directory.
- `api.os.remove(path)`: Removes the specified file.
- `api.os.rename(src, dst)`: Renames a file or directory from `src` to `dst`.
- `api.os.pathExists(path)`: Checks if the specified path exists.
- `api.os.isDir(path)`: Checks if the specified path is a directory.
- `api.os.isFile(path)`: Checks if the specified path is a file.
- `api.os.makeDirs(path)`: Creates directories recursively.
- `api.os.removeDir(path)`: Removes the specified directory.
- `api.os.pathJoin(*paths)`: Joins one or more path components.
- `api.os.pathSplit(path)`: Splits the specified path into a pair (head, tail).
- `api.os.pathBasename(path)`: Returns the base name of the specified path.
- `api.os.pathDirname(path)`: Returns the directory name of the specified path.
- `api.os.pathAbsolute(path)`: Returns the absolute path of the specified path.
- `api.os.pathGetSize(path)`: Returns the size of the specified file.
- `api.os.pathIsLink(path)`: Checks if the specified path is a symbolic link.

### HtmlApi

- `api.html.serveHtml(html)`: Serves the given HTML content with a 200 status code.
- `api.html.builder()`: Returns an instance of the `HtmlBuilder` class for creating HTML structures.

### UtilityApi

- `api.util.sleep(seconds)`: Pauses execution for the specified number of seconds.
- `api.util.hashData(data, algorithm="sha256")`: Hashes the input data using the specified algorithm (default is SHA-256).
- `api.util.validateEmail(email)`: Validates the format of the given email address.
- `api.util.base64Encode(data)`: Encodes the input data to Base64.
- `api.util.base64Decode(data)`: Decodes Base64 encoded data.
- `api.util.timestamp()`: Returns the current UTC timestamp in ISO format.
- `api.util.uuid()`: Generates and returns a new UUID.
- `api.util.urlEncode(data)`: Encodes a string for URL usage.
- `api.util.urlDecode(data)`: Decodes a URL-encoded string.
- `api.util.generateRandomString(length)`: Generates a random alphanumeric string of the specified length.
- `api.util.getIPAddress()`: Returns the IP address of the current machine.
- `api.util.dnsLookup(domain)`: Performs a DNS lookup for the specified domain.
- `api.util.generateSlug(text)`: Converts a string into a URL-friendly slug.
- `api.util.getCpuUsage()`: Returns the current CPU usage percentage.
- `api.util.getMemoryUsage()`: Returns the current memory usage in kilobytes.
