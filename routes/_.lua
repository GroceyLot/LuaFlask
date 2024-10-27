-- Define and return the main function
return function(requestData)
    local htmlBuilder = api.html.builder()

    -- Build HTML content using HtmlBuilder API with additional dynamic elements
    htmlBuilder:doctype() -- Define the document type
    :open("html") -- Open the <html> tag
    :open("head") -- Open the <head> tag
    :title("Enhanced LuaFlask Example") -- Set the title of the document
    :meta({
        charset = "UTF-8"
    }) -- Set the character set
    :link({ -- Link to external stylesheet
        rel = "stylesheet",
        href = "/static/styles.css"
    }):close() -- Close the <head> tag
    :open("body") -- Open the <body> tag
    :open("h1") -- Open the <h1> tag
    :plain("Welcome to the LuaFlask Example!") -- Add welcome message
    :close() -- Close the <h1> tag
    :open("p") -- Open the first <p> tag
    :plain("This page showcases dynamic features built with Lua!") -- Add description
    :close() -- Close the first <p> tag

    -- Dynamic Date and Time
    htmlBuilder:open("p") -- Open a new <p> tag for date and time
    :plain("Current UTC Date and Time: " .. api.util.timestamp()) -- Display current timestamp
    :close() -- Close the <p> tag

    -- Random Number Generation
    htmlBuilder:open("h2") -- Open <h2> for random number section
    :plain("Random Number") -- Add section title
    :close() -- Close the <h2> tag
    :open("p") -- Open a new <p> tag for random number display
    :plain("Here's a random number for you: " .. tostring(math.random(1, 100))) -- Display random number
    :close() -- Close the <p> tag

    -- UUID Generation
    htmlBuilder:open("h2") -- Open <h2> for UUID generator section
    :plain("UUID Generator") -- Add section title
    :close() -- Close the <h2> tag
    :open("p") -- Open a new <p> tag for UUID display
    :plain("Generated UUID: " .. api.util.uuid()) -- Display generated UUID
    :close() -- Close the <p> tag

    -- Email Validation Example
    htmlBuilder:open("h2") -- Open <h2> for email validation section
    :plain("Email Validation") -- Add section title
    :close() -- Close the <h2> tag
    :open("p") -- Open a new <p> tag for email validation message
    :plain("Testing 'test@example.com': ") -- Display email being tested
    :close() -- Close the <p> tag
    :open("p") -- Open another <p> tag for validation result
    :plain(api.util.validateEmail("test@example.com") and "Valid!" or "Invalid!") -- Show validation result
    :close() -- Close the <p> tag

    -- Interactive Form with Lua-Processed Input
    htmlBuilder -- Display CPU and Memory Usage
    :open("h2") -- Open <h2> for system information section
    :plain("System Information") -- Add section title
    :close() -- Close the <h2> tag
    :open("p") -- Open a new <p> tag for CPU usage
    :plain("CPU Usage: " .. api.util.getCpuUsage() .. "%") -- Display CPU usage
    :close() -- Close the <p> tag
    :open("p") -- Open another <p> tag for memory usage
    :plain("Memory Usage: " .. api.util.getMemoryUsage() / 1024 .. " MB") -- Display memory usage
    :close() -- Close the <p> tag
    :open("a", {href="/test.shtml"}) -- Open a new <a> tag for SHTML test page
    :plain("Go to the other test page") -- Add link text
    :close() -- Close the <a> tag
    :close() -- Close the <body> tag
    :close() -- Close the <html> tag

    local htmlContent = htmlBuilder:finish() -- Finish building HTML content

    -- Return the HTML response
    return api.html.serveHtml(htmlContent) -- Serve the generated HTML content
end
