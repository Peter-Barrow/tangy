# API Reference

## Buffers
### :::tangy.Buffer
    options:
        show_root_heading: true
        show_source: false

### :::tangy.BufferStandard
    options:
        show_root_heading: true
        show_source: false

### :::tangy.BufferClocked
    options:
        show_root_heading: true
        show_source: false

!!! example "Example with the Python handler"
    === "docs/my_page.md"
        ```md
        # Documentation for `MyClass`

        ::: tangy.BufferStandard
            handler: python
            options:
              members:
                - lower_bound
              show_root_heading: false
              show_source: false
        ```

    === "mkdocs.yml"
        ```yaml
        nav:
          - "My page": my_page.md
        ```


    === "Result"
        <h3 id="documentation-for-myclass" style="margin: 0;">Documentation for <code>MyClass</code></h3>
        <div><div><p>Print print print!</p><div><div>
        <h4 id="mkdocstrings.my_module.MyClass.method_a">
        <code class="highlight language-python">
        method_a<span class="p">(</span><span class="bp">self</span><span class="p">)</span> </code>
        </h4><div>
        <p>Print A!</p></div></div><div><h4 id="mkdocstrings.my_module.MyClass.method_b">
        <code class="highlight language-python">
        method_b<span class="p">(</span><span class="bp">self</span><span class="p">)</span> </code>
        </h4><div><p>Print B!</p></div></div></div></div></div>


## Measurements
:::tangy.singles
    options:
        show_root_heading: true
        show_source: false

## File Readers
### :::tangy.PTUFile
    options:
        members:
            - records
            - read
            - read_seconds
        show_root_heading: true
        show_source: false
