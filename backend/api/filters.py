def recipe_filter(queryset, name, value):

    if name == 'author':
        return queryset.filter(author__username=value)

    if name == 'tags':
        tags = value.split(',')
        return queryset.filter(tags__name__in=tags)

    return queryset
