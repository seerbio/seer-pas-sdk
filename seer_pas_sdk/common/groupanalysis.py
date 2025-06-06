def validate_contrast(contrast, ngroups):
    """
    Validate the contrast.

    Parameters
    ----------
    contrast : list or tuple
        The contrast to validate.

    ngroups : int
        The number of groups in the contrast.

    Returns
    -------
    list
        The validated contrast.

    Raises
    ------
    TypeError
        If contrast is not a list or tuple.
        If contrast is not a collection of integers.
    ValueError
        If contrast has less than 2 elements.
        If contrast does not have the same number of elements as ngroups.
        If contrast is not a list of -1, 0, or 1.
        If contrast does not have exactly one 1.
        If contrast does not have exactly one -1.
    """
    if not isinstance(contrast, (list, tuple)):
        raise TypeError("contrast must be a list or tuple")
    if len(contrast) < 2:
        raise ValueError("contrast must have at least 2 elements")
    if not all(isinstance(i, int) for i in contrast):
        raise TypeError("contrast must be a list of integers")
    if not len(contrast) == ngroups:
        raise ValueError(f"contrast {contrast} must have {ngroups} elements")
    if not all([i in range(-1, 2) for i in contrast]):
        raise ValueError(f"contrast {contrast} must be a list of -1, 0, or 1")

    # Check that the contrast has exactly one 1 and one -1
    count_1 = 0
    count_neg1 = 0

    for item in contrast:
        if item == 1:
            count_1 += 1
        elif item == -1:
            count_neg1 += 1

    if count_1 != 1:
        raise ValueError(f"contrast {contrast} must have exactly one 1")
    if count_neg1 != 1:
        raise ValueError(f"contrast {contrast} must have exactly one -1")
    return contrast
