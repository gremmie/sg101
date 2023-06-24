import jinja2


def main():
    print('Hello World')

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('ssg101'),
        )
    template = env.get_template('home.html')

    with open('output/home.html', 'w') as fp:
        fp.write(template.render())


if __name__ == '__main__':
    main()
