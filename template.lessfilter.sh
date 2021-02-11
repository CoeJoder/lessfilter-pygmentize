#!/bin/bash
# uses Pygments v{{ pygments_version }} for syntax highlighting on applicable file types
for path in "$@"; do
    # match by known filenames
    filename=$(basename "$path")
    case "$filename" in
        {{ misc_shell_filenames }})
            # shell lexer
            pygmentize -f 256 -O style="$PYGMENTIZE_STYLE" -l sh "$path"
            ;;
        {{ recognized_filenames }})
            # filename recognized
            pygmentize -f 256 -O style="$PYGMENTIZE_STYLE" "$path"
            ;;
        *)
            ext=$([[ "$filename" = *.* ]] && echo ".${filename##*.}" || echo '')
            case "$ext" in
                {{ recognized_extensions }})
                    # extension recognized
                    pygmentize -f 256 -O style="$PYGMENTIZE_STYLE" "$path"
                    ;;
                *)
                    # unrecognized filename/extension
                    # attempt to parse the lexer from the shebang if it exists
                    lexer=$(head -n 1 "$path" |grep "^#\!" |awk -F" " \
'match($1, /\/(\w*)$/, a) {if (a[1]!="env") {print a[1]} else {print $2}}')
                    case "$lexer" in
                        node|nodejs)
                            # workaround for lack of Node.js lexer alias
                            pygmentize -f 256 -O style="$PYGMENTIZE_STYLE" \
                                -l js "$path"
                            ;;
                        "")
                            # fall-back to plain text
                            exit 1
                            ;;
                        *)
                            # use lexer alias parsed from the shebang
                            pygmentize -f 256 -O style="$PYGMENTIZE_STYLE" \
                                -l "$lexer" "$path"
                            ;;
                    esac
                    ;;
            esac
            ;;
    esac
done
exit 0

