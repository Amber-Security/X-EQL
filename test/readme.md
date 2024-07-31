CEP特性用例：

复杂时间的处理 严格顺序 时间约束 时间限制 重复特性 遇到一个匹配跳过后面的匹配

近邻关系  宽松状态

检测连续的时间 或者不连续但后发生的时间 匹配超时

针对NFA单独测试

\*\*   testNFACompilerUniquePatternName\*\*:

这个测试方法旨在验证当定义的模式中存在重复的模式名称时，编译器是否会抛出 `MalformedPatternException` 异常，并且异常消息应包含 "Duplicate pattern name: start. Names must be unique."。

测试使用了一个不正确的模式 `invalidPattern`，其中包含两个使用相同名称 "start" 的模式。根据预期，编译器应该在编译这个模式时抛出异常。

*   **testNFACompilerPatternEndsWithNotFollowedBy**:

    这个测试方法旨在验证当模式规范的最后一个部分是 `notFollowedBy` 时，编译器是否会抛出 `MalformedPatternException` 异常，并且异常消息应包含 "NotFollowedBy is not supported without windowTime as a last part of a Pattern!"。

    测试使用了另一个不正确的模式 `invalidPattern`，其中模式的最后部分是 `notFollowedBy`，这在特定的 NFA 规范中可能是不允许的。根据预期，编译器应该在编译这个模式时抛出异常。

testNFACompilerWithSimplePattern

创建 简单 中间结束状态

建了一个复杂的事件模式 (`Pattern`)，它包含了以下步骤：

*   从名为 "start" 的状态开始，该状态满足 `startFilter` 条件。
*   然后跟随一个名为 "middle" 的状态，该状态是 `SubEvent` 的子类。
*   最后跟随一个名为 "end" 的状态，该状态满足 `endFilter` 条件。

将 NFA 的状态映射到一个 `HashMap` 中，方便后续验证每个状态的属性和转移。

确保起始状态存在于状态映射中，并验证它是起始状态。然后，验证它的转移状态 (`"middle"`) 和转移动作 (`StateTransitionAction.TAKE`)。

确保特殊的结束状态存在于状态映射中，并验证它是最终状态 (`isFinal()`)，并且没有其他的状态转移。

这段测试代码的主要目的是确保编译器能够正确地将复杂的事件模式转换为 NFA，并验证每个状态的属性和状态转移的正确性。这有助于确保 NFA 编译器在处理复杂事件模式时的正确性和一致性。

testNFACompilerPatternNotFollowedByWithIn()

定义了一个模式 `pattern`，开始于名称为 "start" 的状态，使用 `startFilter` 进行过滤。接着使用 `notFollowedBy("middle")` 指定在遇到 "middle" 事件之后不应继续匹配模式，然后再使用 `endFilter` 进行结束状态的过滤条件。最后，定义模式的时间限制为 1 毫秒。

获取编译后的 NFA 的所有状态，并断言状态的数量

testNoUnnecessaryStateCopiesCreated()

复杂的模式 `pattern`，从 "start" 状态开始，使用 `startFilter` 进行过滤，然后定义了一系列的模式匹配条件，包括 `notFollowedBy("not")`、`followedBy("oneOrMore")`、`oneOrMore()` 等，最后以 `followedBy("end")` 结束，并使用 `endFilter` 进行结束状态的过滤。

NFA 编译器是否能正确地生成期望的状态结构，并且确保不会因为误操作或设计缺陷而创建多余的状态副本。通过检查特定名称的状态数量，特别是最终的结束状态，可以确认编译器在处理复杂模式时的行为是否符合预期。

testSkipToNotExistsMatchingPattern()

指定的跳转目标状态名（"midd"）在模式中并不存在的情况。让我们逐步解释这段代码的功能和逻辑：

*   创建了一个名为 `invalidPattern` 的模式对象。在模式的起始处使用了 `AfterMatchSkipStrategy.skipToLast("midd")`，这表示如果后续匹配失败，应该跳转到名称为 "midd" 的状态。然而，在这个模式定义中，不存在名为 "midd" 的状态。

1.  调用 `compile` 方法，传入无效的模式 `invalidPattern` 和 `false` 参数，用于编译模式并预期抛出异常。
2.  测试逻辑分析
    *   **测试目标**: 测试的目的是验证当在模式定义中指定了 `AfterMatchSkipStrategy.skipToLast()` 的目标状态名不存在时，是否会抛出预期的异常 `MalformedPatternException`。
    *   **模式定义分析**:

        *   模式从 "start" 开始，定义了一系列条件和转移，包括 "middle" 和 "end" 状态，但没有 "midd" 状态。
        *   `AfterMatchSkipStrategy.skipToLast("midd")` 告诉引擎如果匹配失败就跳到 "midd" 状态，然而 "midd" 状态在模式中不存在，这会导致模式定义不完整或不正确。
    *   **预期结果**: 预期测试会抛出 `MalformedPatternException` 异常，并且异常消息应包含指定的错误信息，确保测试覆盖了模式定义中的异常情况。
        这种测试对于确保模式定义的完整性和正确性非常重要，特别是涉及到复杂的模式匹配和跳转策略时。通过这样的单元测试，可以及早发现和修复模式定义中可能存在的问题，确保系统在实际运行中的稳定性和可靠性。
3.  用于验证在定义复杂事件处理模式时，如果指定的跳转目标状态不存在，是否能够正确地抛出 `MalformedPatternException` 异常，并且异常消息包含特定的错误信息。
    *   测试设置：

        *   `expectedException.expect(MalformedPatternException.class);` 设置了预期的异常类型为 `MalformedPatternException`，表示预期在测试中会抛出这种异常。
        *   `expectedException.expectMessage(...);` 设置了异常消息的预期内容，确保异常消息包含特定的文本 "The pattern name specified in AfterMatchSkipStrategy can not be found in the given Pattern"。
    *   模式定义 (`invalidPattern`)：

        *   使用 `Pattern.begin("start", AfterMatchSkipStrategy.skipToLast("midd"))` 开始定义一个模式。其中 `AfterMatchSkipStrategy.skipToLast("midd")` 指定了一个跳过策略，在模式匹配失败后跳转到状态为 "midd" 的位置。
        *   `where(SimpleCondition.of(value -> value.getName().contains("a")))` 定义了一个条件，要求事件的名称包含字母 "a"。
        *   `.next("middle")` 表示在满足条件后，模式应该接着匹配 "middle" 状态。
        *   `where(SimpleCondition.of(value -> value.getName().contains("d")))` 继续定义了一个条件，要求事件的名称包含字母 "d"。
        *   `.oneOrMore().optional()` 指定了一个可选的重复匹配，表示可以有一次或多次的 "middle" 状态。
        *   `.next("end")` 定义了最后的状态转移，匹配到 "end" 状态。
        *   `where(SimpleCondition.of(value -> value.getName().contains("c")))` 最后再定义了一个条件，要求事件的名称包含字母 "c"。

testCheckingEmptyMatches()

1.  **测试目的**：

    *   这是一个用于测试模式是否能够产生空匹配的单元测试方法。在复杂事件处理中，模式可以定义为可以匹配一系列事件序列，有时可能允许为空序列的情况。这个测试方法通过不同的模式组合来验证 `canProduceEmptyMatches` 方法的行为是否符合预期。
2.  **测试设置**：

    *   `assertThat(..., is(true));` 和 `assertThat(..., is(false));` 断言用于验证不同模式下的预期结果。
3.  **模式定义**：

    *   `Pattern.begin("a").optional()`：定义了一个以事件 "a" 开始的模式，并且这个事件是可选的，即模式可以匹配 "a" 或者空序列。
    *   `Pattern.begin("a").oneOrMore().optional()`：以事件 "a" 开始的模式，后面跟随一次或多次的 "a" 事件，然后整体是可选的，因此模式可以匹配一连串的 "a" 或者空序列。
    *   `Pattern.begin("a").oneOrMore().optional().next("b").optional()`：以事件 "a" 开始的模式，后面跟随一次或多次的 "a" 事件，然后接着事件 "b"，最后整体是可选的，所以模式可以匹配 "a"、"aa"、"aab"、"ab" 或者空序列。
    *   `Pattern.begin("a")`：定义了一个以事件 "a" 开始的模式，要求至少匹配一个 "a"。
    *   `Pattern.begin("a").oneOrMore()`：以事件 "a" 开始的模式，后面跟随一次或多次的 "a" 事件，不允许为空序列。
    *   `Pattern.begin("a").oneOrMore().next("b").optional()`：以事件 "a" 开始的模式，后面跟随一次或多次的 "a" 事件，然后接着事件 "b"，整体是可选的，因此模式可以匹配至少一个 "a" 后跟随 "b"，或者更多 "a" 后跟随 "b"。
4.  **断言**：

    *   `assertThat(NFACompiler.canProduceEmptyMatches(...), is(true));` 断言期望 `canProduceEmptyMatches` 方法返回 `true`，表示模式能够产生空匹配。
    *   `assertThat(NFACompiler.canProduceEmptyMatches(...), is(false));` 断言期望 `canProduceEmptyMatches` 方法返回 `false`，表示模式不能产生空匹配。

### 总结

这段代码通过多个测试案例验证了 `canProduceEmptyMatches` 方法对不同复杂事件处理模式的处理能力。它确保了在定义和分析事件序列模式时，能够正确地判断模式是否允许匹配空序列，这对于复杂事件处理系统的正确性和预期行为测试至关重要。

testWindowTimeCorrectlySet()

1.  **模式定义**：

    *   `Pattern<Event, ?> pattern = ...`：在这里，定义了一个复杂事件处理模式。这个模式由一系列事件组成，顺序为 "start" -> "middle" -> "then" -> "end"，并且每两个事件之间有特定的时间限制。
2.  **事件模式的构建**：

    *   `Pattern.<Event>begin("start")`：开始定义事件模式，以事件 "start" 开始。
    *   `.followedBy("middle")`：紧接着事件 "start" 后必须是事件 "middle"。
    *   `.within(Time.seconds(10))`：定义了一个时间窗口，要求 "start" 和 "middle" 事件之间的时间间隔不超过 10 秒。
    *   `.followedBy("then")`：紧接着事件 "middle" 后必须是事件 "then"。
    *   `.within(Time.seconds(20))`：定义了另一个时间窗口，要求 "middle" 和 "then" 事件之间的时间间隔不超过 20 秒。
    *   `.followedBy("end")`：紧接着事件 "then" 后必须是事件 "end"。

系列顺序事件和相应的时间限制来检查模式编译后的行为是否符合预期。通过这种方式，可以确保在事件处理系统中，定义的时间窗口能够正确地约束事件序列的时间间隔，从而实现预期的事件匹配和处理逻辑。

testWindowTimesCorrectlySet()

*   `Pattern<Event, ?> pattern = ...`：定义了一个复杂事件处理模式。
*   `.within(Time.seconds(10), WithinType.PREVIOUS_AND_CURRENT)`：设置了在 "start" 和 "middle" 事件之间的时间窗口为 10 秒，并指定了时间窗口类型为 `PREVIOUS_AND_CURRENT`，表示当前事件和前一个事件的时间间隔都要考虑。
*   `.within(Time.seconds(20), WithinType.PREVIOUS_AND_CURRENT)`：设置了在 "middle" 和 "then" 事件之间的时间窗口为 20 秒，同样指定了时间窗口类型为 `PREVIOUS_AND_CURRENT`。
*   `.followedBy("end")`：定义了事件模式的最后一个事件为 "end"。

这段代码通过定义复杂事件处理模式，并编写单元测试来确保模式中各个时间窗口的设置是否正确。通过比较预期的时间窗口设置与实际的时间窗口设置，来验证程序逻辑的正确性。这种测试方法对于事件驱动的系统或流处理系统中的时间相关逻辑非常重要，能有效保证处理逻辑的准确性和可靠性。

testMultipleWindowTimeWithZeroLength(

1.  `Pattern<Event, ?> pattern = ...`：定义了一个复杂事件处理模式。

    *   `.within(Time.seconds(10))`：设置了在 "start" 和 "middle" 事件之间的时间窗口为 10 秒。
    *   `.within(Time.seconds(0))`：设置了在 "middle" 和 "then" 事件之间的时间窗口为 0 秒，即无时间窗口限制。
    *   `.followedBy("end")`：定义了事件模式的最后一个事件为 "end"。
2.  在复杂事件处理模式中，当设置多个时间窗口时，其中一个时间窗口的长度为零。
3.  通过将模式编译为 NFA，并检查工厂返回的时间窗口长度是否为零，来验证系统对于零长度时间窗口的正确处理。

这种测试可以确保系统在面对不同时间窗口设置时，能够正确地识别和处理零长度时间窗口的场景，避免可能出现的逻辑错误或异常行为

testCheckPatternWindowTimes()

*   `Pattern.<Event>begin("start")`：定义了一个复杂事件处理模式的起始事件为 "start"。
*   `.followedBy("middle")`：指定 "start" 事件之后紧跟着 "middle" 事件。
*   `.within(Time.seconds(3), WithinType.PREVIOUS_AND_CURRENT)`：设置 "start" 和 "middle" 事件之间的时间窗口为 3 秒，并指定时间窗口类型为 `PREVIOUS_AND_CURRENT`，即考虑前一个和当前事件。
*   `.followedBy("then")`：指定 "middle" 事件之后紧跟着 "then" 事件。
*   `.within(Time.seconds(1), WithinType.PREVIOUS_AND_CURRENT)`：设置 "middle" 和 "then" 事件之间的时间窗口为 1 秒，同样指定时间窗口类型为 `PREVIOUS_AND_CURRENT`。
*   `.followedBy("end")`：定义了事件模式的最后一个事件为 "end"。
*   `.within(Time.milliseconds(2))`：设置 "then" 和 "end" 事件之间的时间窗口为 2 毫秒。



AfterMatchSkipITCase\:nfa特性具体的测试用例

testNoSkip()             &#x20;

```java
javaCopy CodeEvent a1 = new Event(1, "a", 0.0);
Event a2 = new Event(2, "a", 0.0);
Event a3 = new Event(3, "a", 0.0);
Event a4 = new Event(4, "a", 0.0);
Event a5 = new Event(5, "a", 0.0);
Event a6 = new Event(6, "a", 0.0);

List<StreamRecord<Event>> streamEvents = new ArrayList<>();
streamEvents.add(new StreamRecord<Event>(a1));
streamEvents.add(new StreamRecord<Event>(a2));
streamEvents.add(new StreamRecord<Event>(a3));
streamEvents.add(new StreamRecord<Event>(a4));
streamEvents.add(new StreamRecord<Event>(a5));
streamEvents.add(new StreamRecord<Event>(a6));
```

*   创建了一个事件模式 `pattern`：

    *   `begin("start", AfterMatchSkipStrategy.noSkip())`：定义了模式的起始点为 "start"，并设置匹配策略为 `noSkip()`，即在匹配到事件后不跳过。
    *   `.where(SimpleCondition.of(value -> value.getName().equals("a")))`：指定事件类型为 "a" 的条件。
    *   `.times(3)`：指定匹配的次数为 3 次，即查找连续出现三次 "a" 类型的事件序列。

1.  javaCopy Code

    `comparePatterns( resultingPatterns, Lists.newArrayList( Lists.newArrayList(a1, a2, a3), Lists.newArrayList(a2, a3, a4), Lists.newArrayList(a3, a4, a5), Lists.newArrayList(a4, a5, a6)));`

    *   调用 `comparePatterns` 方法，比较实际的匹配结果 `resultingPatterns` 与预期的模式序列列表。
    *   预期结果是包含了所有连续出现三次 "a" 的事件序列，例如 `(a1, a2, a3)`，`(a2, a3, a4)` 等。

### 测试目的和含义

该测试方法用于验证在给定的事件流中，是否能够正确地识别和匹配连续出现三次 "a" 类型事件的模式。通过使用 Flink CEP 库提供的测试工具 `NFATestHarness`，可以模拟实时流数据，并验证定义的事件模式是否能够按预期进行匹配。



testNoSkipWithFollowedByAny

这段代码是用于测试复杂事件处理（CEP）的功能，具体来说，是使用 Apache Flink CEP 库来定义和验证事件流中的模式匹配行为。让我们逐步解析代码的测试目的和含义：

### 目的：

1.  **测试复杂事件模式匹配**：

    *   通过定义事件流中的模式，测试系统是否能够正确地识别和匹配预期的事件序列。
2.  **验证跳过策略的影响**：

    *   代码中包含两个测试方法，分别使用不同的跳过策略进行模式匹配测试，以验证不同策略对模式匹配结果的影响。

### 含义：

1.  **`testNoSkipWithFollowedByAny` 方法**：

    *   使用 `AfterMatchSkipStrategy.noSkip()` 策略进行测试。
    *   定义了一个模式，要求以事件 "a" 开始，然后紧跟任何事件 "b"。
    *   预期的匹配模式包括 `(a1, b1)`、`(a1, b2)` 和 `(a2, b2)`。
2.  **`testSkipToNextWithFollowedByAny` 方法**：

    *   使用 `AfterMatchSkipStrategy.skipToNext()` 策略进行测试。
    *   同样定义了以事件 "a" 开始，紧跟任何事件 "b" 的模式。
    *   预期的匹配模式包括 `(a1, b1)` 和 `(a2, b2)`。
3.  **`TwoVariablesFollowedByAny` 类**：

    *   包含静态事件实例 `a1`, `b1`, `a2`, `b2`，分别代表不同的事件。
    *   `compute` 方法负责构建事件流 `streamEvents`，并定义了一个复杂事件模式 `Pattern`。
    *   使用 `NFATestHarness` 进行模式测试和验证，它是 Flink CEP 提供的测试工具，可以模拟事件流并检查模式匹配的正确性。

### 总结：

这段代码的主要目的是测试和验证在事件流中使用 Flink CEP 库定义的复杂事件模式。通过两种不同的跳过策略，确保系统能够正确识别和处理定义的事件模式，以及验证预期的匹配结果。这种方法非常有助于在实际应用中，特别是在实时数据处理中，确保系统能够按照预期方式处理和响应事件流。



testNoSkipWithQuantifierAtTheEnd()

这段代码是用于测试复杂事件处理（CEP）中的模式匹配功能，具体来说，它涉及到使用 Apache Flink CEP 库来定义和验证事件流中的模式匹配行为。让我们逐步解析这段代码的测试目的和含义：

### 测试目的：

1.  **测试不跳过策略下的量词在模式末尾**：

    *   通过调用 `QuantifierAtEndOfPattern.compute(AfterMatchSkipStrategy.noSkip())` 方法来测试。
    *   目的是验证在模式的末尾使用量词（即重复事件 "b"）时，系统能否正确识别和匹配事件序列。

### 方法和验证：

1.  **`testNoSkipWithQuantifierAtTheEnd` 方法**：

    *   使用 `AfterMatchSkipStrategy.noSkip()` 策略进行测试，这意味着测试将不会跳过任何匹配。
    *   `QuantifierAtEndOfPattern.compute()` 方法返回一个 `List<List<Event>>`，表示匹配的模式序列。
    *   预期的结果是验证多种可能的模式序列：

        *   包含事件序列 `(a1, b1, b2, b3)`
        *   包含事件序列 `(a1, b1, b2)`
        *   包含事件序列 `(a1, b1)`
2.  **`comparePatterns` 方法**：

    *   用于比较预期结果与实际结果的模式序列，确保模式匹配的准确性和完整性。
3.  **`QuantifierAtEndOfPattern` 类**：

    *   包含静态事件实例 `a1`, `b1`, `b2`, `b3`，代表不同的事件。
    *   `compute` 方法负责构建事件流，并定义了一个复杂事件模式，以便测试系统可以正确地识别和处理这些事件序列。

### 总结：

这段代码的主要目的是通过使用 Flink CEP 库来测试和验证在事件流中定义的复杂事件模式。通过测试不同的模式匹配情况，特别是在模式末尾使用量词的情况下，确保系统能够正确地识别、匹配和处理预期的事件序列。这种测试对于确保在实际应用中，特别是在处理实时数据时，系统能够按照预期的方式进行模式识别和响应非常重要。



这段代码的主要目的是测试在使用 Flink 的复杂事件处理（CEP）库时，特别是在模式的末尾使用量词（oneOrMore()）时，如何应用跳过策略以及如何处理事件流。让我们详细解释其测试目的和代码含义：

### 测试方法 `testSkipToNextWithQuantifierAtTheEnd`

```
javaCopy Codepublic void testSkipToNextWithQuantifierAtTheEnd() throws Exception {
    List<List<Event>> resultingPatterns =
            QuantifierAtEndOfPattern.compute(AfterMatchSkipStrategy.skipToNext());

    comparePatterns(
            resultingPatterns,
            Lists.<List<Event>>newArrayList(
                    Lists.newArrayList(
                            QuantifierAtEndOfPattern.a1, QuantifierAtEndOfPattern.b1)));
}

```

*   **测试目的**：

    *   确定在模式中使用 `oneOrMore()` 量词时，如果在模式的末尾遇到匹配的情况，系统是否能够正确地跳过到下一个可能的匹配模式序列。
    *   使用 `AfterMatchSkipStrategy.skipToNext()` 策略，该方法是指在找到一个匹配模式后，直接跳到下一个可能的匹配模式，而不是等待可能的重叠或连续模式。



testSkipToNextWithQuantifierAtTheEnd()

### `QuantifierAtEndOfPattern` 类

```
javaCopy Codestatic class QuantifierAtEndOfPattern {

    static Event a1 = new Event(1, "a", 0.0);
    static Event b1 = new Event(2, "b", 0.0);
    static Event b2 = new Event(4, "b", 0.0);
    static Event b3 = new Event(5, "b", 0.0);

    private static List<List<Event>> compute(AfterMatchSkipStrategy skipStrategy)
            throws Exception {
        List<StreamRecord<Event>> streamEvents = new ArrayList<>();

        // 添加事件流
        streamEvents.add(new StreamRecord<>(a1));
        streamEvents.add(new StreamRecord<>(b1));
        streamEvents.add(new StreamRecord<>(b2));
        streamEvents.add(new StreamRecord<>(b3));

        // 定义模式
        Pattern<Event, ?> pattern =
                Pattern.<Event>begin("start")
                        .where(SimpleCondition.of(value -> value.getName().equals("a")))
                        .next("end")
                        .where(SimpleCondition.of(value -> value.getName().equals("b")))
                        .oneOrMore();

        // 使用NFATestHarness进行模式匹配测试
        NFATestHarness nfaTestHarness =
                NFATestHarness.forPattern(pattern)
                        .withAfterMatchSkipStrategy(skipStrategy)
                        .build();

        // 返回匹配到的模式序列列表
        return nfaTestHarness.feedRecords(streamEvents);
    }
}

```

*   **`QuantifierAtEndOfPattern.compute` 方法**：

    *   创建一个包含事件流的 `streamEvents` 列表，其中包括了预定义的事件序列 `a1`, `b1`, `b2`, `b3`。
    *   使用 Flink CEP 的 `Pattern` 类定义一个模式，该模式要求从事件 "a" 开始，然后至少出现一个或多个事件 "b"。
    *   使用 `NFATestHarness` 进行模式匹配测试，设置了在找到匹配后立即跳过到下一个可能的匹配模式的策略。
    *   返回匹配到的模式序列列表，以供进一步验证和比较。

### 总结

这段代码通过测试的方式确保系统在处理复杂事件模式时的正确性和效率。特别是在模式的末尾使用量词时，能够正确地跳过已经匹配的模式并继续寻找下一个可能的模式序列，从而提高了系统在实时数据流处理中的应用能力和性能。



testSkipPastLast

这段代码是一个测试方法，用于验证在使用 Flink CEP 库处理复杂事件模式时，特别是在定义模式中使用了 `times()` 方法时的行为。让我们分析其测试目的和代码含义：

### 测试方法 `testSkipPastLast`

```java
javaCopy Codepublic void testSkipPastLast() throws Exception {
    List<StreamRecord<Event>> streamEvents = new ArrayList<>();

    Event a1 = new Event(1, "a", 0.0);
    Event a2 = new Event(2, "a", 0.0);
    Event a3 = new Event(3, "a", 0.0);
    Event a4 = new Event(4, "a", 0.0);
    Event a5 = new Event(5, "a", 0.0);
    Event a6 = new Event(6, "a", 0.0);

    streamEvents.add(new StreamRecord<Event>(a1));
    streamEvents.add(new StreamRecord<Event>(a2));
    streamEvents.add(new StreamRecord<Event>(a3));
    streamEvents.add(new StreamRecord<Event>(a4));
    streamEvents.add(new StreamRecord<Event>(a5));
    streamEvents.add(new StreamRecord<Event>(a6));

    Pattern<Event, ?> pattern =
            Pattern.<Event>begin("start", AfterMatchSkipStrategy.skipPastLastEvent())
                    .where(SimpleCondition.of(value -> value.getName().equals("a")))
                    .times(3);

    NFATestHarness nfaTestHarness = NFATestHarness.forPattern(pattern).build();

    List<List<Event>> resultingPatterns = nfaTestHarness.feedRecords(streamEvents);

    comparePatterns(
            resultingPatterns,
            Lists.newArrayList(Lists.newArrayList(a1, a2, a3), Lists.newArrayList(a4, a5, a6)));
}

```

### 分析

*   **测试目的**：

    *   确保当在事件流中定义的模式中，通过 `times(3)` 方法指定匹配事件 "a" 的次数为三次时，系统能够正确地处理模式的跳过策略。
    *   使用 `AfterMatchSkipStrategy.skipPastLastEvent()` 策略，该策略指示在匹配到完整的模式后，跳过模式中最后一个事件之后的所有事件，直接从下一个事件开始尝试匹配新的模式序列。
*   **代码含义**：

    *   创建了一个包含六个事件 `a1` 到 `a6` 的事件流。
    *   定义了一个模式 `Pattern<Event, ?>`，从事件 "a" 开始，要求匹配连续出现三次的 "a"。
    *   使用 `NFATestHarness` 进行模式匹配测试，并构建了模式的验证器。
    *   预期的匹配结果是两个序列，分别是 `{a1, a2, a3}` 和 `{a4, a5, a6}`。
*   **结果比较**：

    *   使用 `comparePatterns` 方法验证实际匹配的模式序列与预期结果是否一致。

### 总结

通过这个测试方法，可以确保系统在处理连续事件模式匹配时的正确性和性能。特别是在定义模式要求特定次数的事件出现时，能够正确地跳过已匹配的部分并继续寻找下一个可能的模式序列，这对于实时流数据处理尤为重要。



testSkipToFirst()

这段代码是用于测试 Flink CEP 库中处理复杂事件模式的行为。让我们分析其测试目的和代码含义：

### 测试方法 `testSkipToFirst`

```
javaCopy Codepublic void testSkipToFirst() throws Exception {
    List<StreamRecord<Event>> streamEvents = new ArrayList<>();

    Event ab1 = new Event(1, "ab", 0.0);
    Event ab2 = new Event(2, "ab", 0.0);
    Event ab3 = new Event(3, "ab", 0.0);
    Event ab4 = new Event(4, "ab", 0.0);
    Event ab5 = new Event(5, "ab", 0.0);
    Event ab6 = new Event(6, "ab", 0.0);

    streamEvents.add(new StreamRecord<Event>(ab1));
    streamEvents.add(new StreamRecord<Event>(ab2));
    streamEvents.add(new StreamRecord<Event>(ab3));
    streamEvents.add(new StreamRecord<Event>(ab4));
    streamEvents.add(new StreamRecord<Event>(ab5));
    streamEvents.add(new StreamRecord<Event>(ab6));

    Pattern<Event, ?> pattern =
            Pattern.<Event>begin("start", AfterMatchSkipStrategy.skipToFirst("end"))
                    .where(SimpleCondition.of(value -> value.getName().contains("a")))
                    .times(2)
                    .next("end")
                    .where(SimpleCondition.of(value -> value.getName().contains("b")))
                    .times(2);

    NFATestHarness nfaTestHarness = NFATestHarness.forPattern(pattern).build();

    List<List<Event>> resultingPatterns = nfaTestHarness.feedRecords(streamEvents);

    comparePatterns(
            resultingPatterns,
            Lists.newArrayList(
                    Lists.newArrayList(ab1, ab2, ab3, ab4),
                    Lists.newArrayList(ab3, ab4, ab5, ab6)));
}

```

### 分析

*   **测试目的**：

    *   确保在事件流中定义的复杂事件模式能够正确地匹配特定的事件序列。
    *   使用 `AfterMatchSkipStrategy.skipToFirst("end")` 策略，该策略指示在匹配到 "end" 事件之前，跳过所有不符合条件的事件，从第一个匹配 "end" 的事件开始尝试新的模式序列。
*   **代码含义**：

    *   创建了一个包含六个事件 `ab1` 到 `ab6` 的事件流，这些事件的名称都包含 "ab"。
    *   定义了一个复杂事件模式 `Pattern<Event, ?>`，其中包括：

        *   从事件名称包含 "a" 的事件开始，要求匹配两次。
        *   然后是一个 "end" 事件，后面跟着一个要求事件名称包含 "b" 的条件，要求匹配两次。
    *   使用 `NFATestHarness` 进行模式匹配测试，并通过 `comparePatterns` 方法验证实际的匹配模式与预期结果是否一致。

### 结论

通过这个测试方法，可以验证 Flink CEP 库在处理复杂事件模式时，特别是在定义模式中使用了跳过策略 `skipToFirst("end")` 的情况下，能够正确地识别和处理符合条件的事件序列。这对于实时数据流处理中的模式识别和事件分析至关重要。



testSkipToLast()

这段代码是用于测试 Flink CEP 库中处理复杂事件模式的行为，具体来说是测试使用 `AfterMatchSkipStrategy.skipToLast("end")` 策略的情况。

### 测试方法 `testSkipToLast`

```java
javaCopy Codepublic void testSkipToLast() throws Exception {
    List<StreamRecord<Event>> streamEvents = new ArrayList<>();

    Event ab1 = new Event(1, "ab", 0.0);
    Event ab2 = new Event(2, "ab", 0.0);
    Event ab3 = new Event(3, "ab", 0.0);
    Event ab4 = new Event(4, "ab", 0.0);
    Event ab5 = new Event(5, "ab", 0.0);
    Event ab6 = new Event(6, "ab", 0.0);
    Event ab7 = new Event(7, "ab", 0.0);

    streamEvents.add(new StreamRecord<Event>(ab1));
    streamEvents.add(new StreamRecord<Event>(ab2));
    streamEvents.add(new StreamRecord<Event>(ab3));
    streamEvents.add(new StreamRecord<Event>(ab4));
    streamEvents.add(new StreamRecord<Event>(ab5));
    streamEvents.add(new StreamRecord<Event>(ab6));
    streamEvents.add(new StreamRecord<Event>(ab7));

    Pattern<Event, ?> pattern =
            Pattern.<Event>begin("start", AfterMatchSkipStrategy.skipToLast("end"))
                    .where(SimpleCondition.of(value -> value.getName().contains("a")))
                    .times(2)
                    .next("end")
                    .where(SimpleCondition.of(value -> value.getName().contains("b")))
                    .times(2);
    NFATestHarness nfaTestHarness = NFATestHarness.forPattern(pattern).build();

    List<List<Event>> resultingPatterns = nfaTestHarness.feedRecords(streamEvents);

    comparePatterns(
            resultingPatterns,
            Lists.newArrayList(
                    Lists.newArrayList(ab1, ab2, ab3, ab4),
                    Lists.newArrayList(ab4, ab5, ab6, ab7)));
}

```

### 分析

*   **测试目的**：

    *   确保在事件流中定义的复杂事件模式能够正确地匹配特定的事件序列。
    *   使用 `AfterMatchSkipStrategy.skipToLast("end")` 策略，该策略指示在匹配到 "end" 事件之前，跳过所有不符合条件的事件，直到最后一个匹配 "end" 的事件。
*   **代码含义**：

    *   创建了一个包含七个事件 `ab1` 到 `ab7` 的事件流，这些事件的名称都包含 "ab"。
    *   定义了一个复杂事件模式 `Pattern<Event, ?>`，其中包括：

        *   从事件名称包含 "a" 的事件开始，要求匹配两次。
        *   然后是一个 "end" 事件，后面跟着一个要求事件名称包含 "b" 的条件，要求匹配两次。
        *   使用 `skipToLast("end")` 策略，确保在匹配到第二个 "end" 事件之前，跳过所有不符合条件的事件，直到最后一个符合条件的 "end" 事件。
*   **测试结果比较**：

    *   使用 `NFATestHarness` 进行模式匹配测试，并通过 `comparePatterns` 方法验证实际的匹配模式与预期结果是否一致。预期结果是两个符合模式的事件序列：`[ab1, ab2, ab3, ab4]` 和 `[ab4, ab5, ab6, ab7]`。

### 结论

通过这个测试方法，可以验证 Flink CEP 库在处理复杂事件模式时，特别是在定义模式中使用了 `skipToLast("end")` 策略的情况下，能够正确地识别和处理符合条件的事件序列，并跳过不必要的事件。这对于实时数据流处理中的模式识别和事件分析具有重要意义。



testSkipPastLast2

这段代码是用于测试 Flink CEP 库中处理复杂事件模式的行为，特别是测试了使用 `AfterMatchSkipStrategy.skipPastLastEvent()` 策略的情况。

### 测试方法 `testSkipPastLast2`

```java
javaCopy Codepublic void testSkipPastLast2() throws Exception {
    List<StreamRecord<Event>> streamEvents = new ArrayList<>();

    Event a1 = new Event(1, "a1", 0.0);
    Event a2 = new Event(2, "a2", 0.0);
    Event b1 = new Event(3, "b1", 0.0);
    Event b2 = new Event(4, "b2", 0.0);
    Event c1 = new Event(5, "c1", 0.0);
    Event c2 = new Event(6, "c2", 0.0);
    Event d1 = new Event(7, "d1", 0.0);
    Event d2 = new Event(7, "d2", 0.0);

    streamEvents.add(new StreamRecord<>(a1));
    streamEvents.add(new StreamRecord<>(a2));
    streamEvents.add(new StreamRecord<>(b1));
    streamEvents.add(new StreamRecord<>(b2));
    streamEvents.add(new StreamRecord<>(c1));
    streamEvents.add(new StreamRecord<>(c2));
    streamEvents.add(new StreamRecord<>(d1));
    streamEvents.add(new StreamRecord<>(d2));

    Pattern<Event, ?> pattern =
            Pattern.<Event>begin("a", AfterMatchSkipStrategy.skipPastLastEvent())
                    .where(SimpleCondition.of(value -> value.getName().contains("a")))
                    .followedByAny("b")
                    .where(SimpleCondition.of(value -> value.getName().contains("b")))
                    .followedByAny("c")
                    .where(SimpleCondition.of(value -> value.getName().contains("c")))
                    .followedBy("d")
                    .where(SimpleCondition.of(value -> value.getName().contains("d")));
    NFATestHarness nfaTestHarness = NFATestHarness.forPattern(pattern).build();

    List<List<Event>> resultingPatterns = nfaTestHarness.feedRecords(streamEvents);

    comparePatterns(
            resultingPatterns, Collections.singletonList(Lists.newArrayList(a1, b1, c1, d1)));
}

```

### 分析

*   **测试目的**：

    *   确保在事件流中定义的复杂事件模式能够正确地匹配特定的事件序列。
    *   使用 `AfterMatchSkipStrategy.skipPastLastEvent()` 策略，该策略指示在匹配到最后一个事件之后，跳过所有不符合条件的事件，直到下一个事件开始新的匹配。
*   **代码含义**：

    *   创建了一个包含八个事件的事件流，包括 `a1` 到 `d2`，每个事件都有不同的名称。
    *   定义了一个复杂事件模式 `Pattern<Event, ?>`，其中包括：

        *   从事件名称包含 "a" 的事件开始，要求匹配一次，并且在匹配到之后，使用 `skipPastLastEvent()` 跳过最后一个事件 `a2`。
        *   然后跟随任何一个包含 "b" 的事件。
        *   接着跟随任何一个包含 "c" 的事件。
        *   最后是一个要求事件名称包含 "d" 的事件。
*   **测试结果比较**：

    *   使用 `NFATestHarness` 进行模式匹配测试，并通过 `comparePatterns` 方法验证实际的匹配模式与预期结果是否一致。预期结果是一个符合模式的事件序列 `[a1, b1, c1, d1]`。

### 结论

通过这个测试方法，可以验证 Flink CEP 库在处理复杂事件模式时，特别是在定义模式中使用了 `skipPastLastEvent()` 策略的情况下，能够正确地识别和处理符合条件的事件序列，并跳过不必要的事件，从而有效地管理和优化事件匹配过程。








未完  待续